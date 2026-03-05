# Async Job Platform

A professional, production-ready asynchronous job processing system built with **Python**, **FastAPI**, **Arq**, and **PostgreSQL**.

This project was created as a training exercise to understand modern backend architectures, asynchronous programming, and background task management in Python.

## Purpose

The **Async Job Platform** handles long-running operations without blocking the user experience. Instead of making a user wait for a heavy task (like generating a CSV report), the API accepts the request, acknowledges it immediately, and processes it in the background.

### Key Features
- **Async API**: Built with FastAPI for high performance.
- **Background Workers**: Uses Arq (Redis-based) for reliable task queueing.
- **Persistence**: PostgreSQL stores job statuses, metadata, and results.
- **Idempotency**: Prevents duplicate job execution using custom headers.
- **Scheduled Jobs**: Supports deferred execution via `run_at`.
- **Clean Architecture**: Organized into layers (API, Service, Repository).
- **Automated Cleanup**: Daily cron job purges jobs and files older than 30 days.

---

## Architecture

### System Overview

```mermaid
graph LR
    Client(["👤 Client"])

    subgraph Platform
        API["🌐 FastAPI\n(API Service)"]
        Worker["⚙️ Arq Worker\n(Background Service)"]
        Redis[("🔴 Redis\n(Message Broker)")]
        Postgres[("🐘 PostgreSQL\n(Persistence)")]
        Files["📁 Shared Files\n(/data/files)"]
    end

    Client -->|"HTTP Request\n(Bearer token)"| API
    API -->|"1. Write job (queued)"| Postgres
    API -->|"2. Enqueue task"| Redis
    Redis -->|"3. Dequeue task"| Worker
    Worker -->|"4. Update status (running → succeeded/failed)"| Postgres
    Worker -->|"5. Write CSV report"| Files
    Client -->|"6. Poll status"| API
    Client -->|"7. Download result"| API
    API -->|"Read job status"| Postgres
    API -->|"Stream file"| Files
```

---

### Job Lifecycle (State Machine)

```mermaid
stateDiagram-v2
    [*] --> queued : POST /jobs/ (job created and enqueued)

    queued --> running : Worker picks up task
    running --> succeeded : CSV generated successfully
    running --> failed : Exception raised

    failed --> running : Retry (up to 2x, backoff 5s / 30s / 2min)

    succeeded --> [*] : Result available for download
    failed --> [*] : Max retries exhausted
```

---

### Layered Architecture

```mermaid
graph TD
    subgraph API Layer
        R["🔗 Routes\nbackend/api/jobs.py"]
        D["🔑 Deps\nbackend/api/deps.py\n(Auth, DB session)"]
    end

    subgraph Service Layer
        S["⚡ JobsService\nbackend/services/jobs.py\n(Business logic, enqueue)"]
    end

    subgraph Repository Layer
        Repo["🗄️ JobsRepo\nbackend/repo/jobs.py\n(Data access)"]
    end

    subgraph Domain Layer
        M["🏗️ Job Model\nbackend/db/models.py\n(SQLAlchemy ORM)"]
        Schema["📋 Schemas\nbackend/domain/jobs.py\n(Pydantic)"]
    end

    subgraph Worker
        W["⚙️ process_job\nworker/main.py"]
        C["🕒 cleanup_old_jobs\n(cron: daily 3 AM UTC)"]
    end

    R -->|Depends| D
    R --> S
    S --> Repo
    S -->|enqueue_job| Redis[(Redis)]
    Repo --> M
    W --> Repo
    C --> Repo
```

---

### Request Flow — POST /jobs/

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI API
    participant DB as PostgreSQL
    participant Redis as Redis Queue
    participant Worker as Arq Worker
    participant FS as File System

    Client->>API: POST /jobs/ (Bearer token, Idempotency-Key?)
    API->>API: Verify API key

    alt Idempotency-Key provided
        API->>DB: Lookup by idempotency_key
        DB-->>API: Existing job or null
        API-->>Client: 201 existing job (no duplicate created)
    end

    API->>DB: INSERT job (status=queued)
    DB-->>API: Job record
    API->>Redis: ENQUEUE process_job(job_id, run_at?)
    API-->>Client: 201 JobRead (status=queued)

    Note over Redis,Worker: Immediate or deferred via run_at

    Redis->>Worker: DEQUEUE task
    Worker->>DB: UPDATE status=running, started_at=now()
    Worker->>FS: Write report_job_id.csv
    Worker->>DB: UPDATE status=succeeded, result_file_path, completed_at

    Client->>API: GET /jobs/id
    API->>DB: SELECT job by id
    API-->>Client: 200 JobRead (status=succeeded)

    Client->>API: GET /jobs/id/download
    API->>FS: Stream file
    API-->>Client: 200 CSV file
```

---

## Directory Structure

```text
py-job-platform/
├── backend/                  # API Service (The Producer)
│   ├── api/
│   │   ├── deps.py           # Auth dependency (Bearer token)
│   │   └── jobs.py           # Route handlers
│   ├── db/
│   │   ├── models.py         # SQLAlchemy Job model & JobStatus enum
│   │   └── session.py        # Async engine & session factory
│   ├── domain/
│   │   └── jobs.py           # Pydantic schemas (JobCreate, JobRead)
│   ├── repo/
│   │   └── jobs.py           # Data Access Layer (Repository pattern)
│   ├── services/
│   │   └── jobs.py           # Business logic & task enqueuing
│   ├── core_config.py        # Settings (env vars via Pydantic)
│   ├── logger.py             # Structured JSON logging (structlog)
│   └── main.py               # FastAPI app entry point
├── worker/
│   └── main.py               # Task definitions, retry config, cron jobs
├── alembic/                  # Database migration scripts
├── docker-compose.yml        # Infrastructure (Postgres, Redis, API, Worker)
├── Dockerfile
└── requirements.txt
```

---

## API Reference

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/jobs/` | Create a new job | ✅ |
| `GET` | `/jobs/` | List jobs (filterable, paginated) | ✅ |
| `GET` | `/jobs/{id}` | Get a single job by ID | ✅ |
| `GET` | `/jobs/{id}/download` | Download the result CSV (when succeeded) | ✅ |
| `GET` | `/health` | Health check | ✅ |

### Query Parameters — `GET /jobs/`

| Param | Type | Description |
|-------|------|-------------|
| `status` | `queued\|running\|succeeded\|failed` | Filter by status |
| `created_after` | `datetime` | Jobs created after timestamp |
| `created_before` | `datetime` | Jobs created before timestamp |
| `limit` | `int` | Max results (default: 100) |
| `offset` | `int` | Pagination offset (default: 0) |

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | ✅ | `Bearer supersecretkey` |
| `Idempotency-Key` | ❌ | Unique string to prevent duplicate job creation |

---

## Getting Started

### Prerequisites
- Docker and Docker Compose

### Running the Platform

```bash
# Clone the repository
git clone https://github.com/your-username/py-job-platform.git
cd py-job-platform

# Start all services
docker-compose up --build
```

Open `http://localhost:8000/docs` for the interactive Swagger UI.

**To authenticate in Swagger:** click the **"Authorize"** button and enter `supersecretkey`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Task Queue | [Arq](https://github.com/samuelcolvin/arq) (Redis-based) |
| Database | [PostgreSQL 15](https://www.postgresql.org/) |
| ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) |
| Logging | [structlog](https://www.structlog.org/) (JSON output) |
| Containerization | [Docker](https://www.docker.com/) + Docker Compose |
| Async DB Driver | asyncpg |
| CI | GitHub Actions (ruff linting) |

---

## Worker Behaviour

### Retry Strategy

| Attempt | Delay |
|---------|-------|
| 1st retry | 5 seconds |
| 2nd retry | 30 seconds |
| Final failure | `status=failed`, `error_message` stored |

### Cron Jobs

| Task | Schedule | Action |
|------|----------|--------|
| `cleanup_old_jobs` | Daily at 3 AM UTC | Deletes jobs and CSV files older than 30 days |

---

## Testing

See [TESTING.md](./TESTING.md) for detailed instructions covering Swagger UI, PowerShell end-to-end tests, and worker log monitoring.

---

## Key Learning Points

- **Asynchronous Programming**: Extensive use of `async`/`await` across the stack.
- **Dependency Injection**: Using FastAPI's `Depends` for database sessions and security.
- **Repository Pattern**: Separating database logic from business logic.
- **Producer-Consumer**: Decoupling request handling from task execution via Redis.
- **Container Orchestration**: Coordinating multiple services with Docker Compose.
- **Error Handling**: Robust retry mechanisms and status tracking for background tasks.
- **Idempotency**: Safe retries without duplicate side effects.
