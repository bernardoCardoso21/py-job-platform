# Async Job Platform

A professional, production-ready asynchronous job processing system built with **Python**, **FastAPI**, **Arq**, and **PostgreSQL**.

This project was created as a training exercise to understand modern backend architectures, asynchronous programming, and background task management in Python.

## Purpose

The **Async Job Platform** is designed to handle long-running operations that shouldn't block the user experience. Instead of making a user wait for a heavy task (like generating a large CSV report) to finish, the API accepts the request, acknowledges it immediately, and processes it in the background.

### Key Features
- **Async API**: Built with FastAPI for high performance.
- **Background Workers**: Uses Arq (Redis-based) for reliable task queueing.
- **Persistence**: PostgreSQL stores job statuses, metadata, and results.
- **Idempotency**: Prevents duplicate job execution using custom headers.
- **Clean Architecture**: Organized into layers (API, Service, Repository) for better maintainability.
- **Automated Cleanup**: Includes a background cron job to purge old data and files.

---

## Architecture

The project follows a **Producer-Consumer** pattern with a layered internal structure:

### High-Level Flow
1. **Producer (API)**: Receives HTTP requests, validates data, saves the job to the database, and pushes a task to Redis.
2. **Broker (Redis)**: Acts as the message queue, holding tasks until a worker is ready.
3. **Consumer (Worker)**: Picks up tasks from Redis, performs the work (e.g., CSV generation), and updates the job status in the database.

### Directory Structure
```text
py-job-platform/
├── backend/            # API Service (The Producer)
│   ├── api/            # API endpoints (FastAPI routers)
│   ├── db/             # Database models (SQLAlchemy) & Session setup
│   ├── domain/         # Data schemas (Pydantic)
│   ├── repo/           # Data Access Layer (Repository pattern)
│   ├── services/       # Business logic & Task enqueuing
│   └── main.py         # API entry point
├── worker/             # Background Service (The Consumer)
│   └── main.py         # Task definitions, retry logic, and cron jobs
├── alembic/            # Database migration scripts
└── docker-compose.yml  # Infrastructure (Postgres, Redis, App services)
```

---

## Getting Started

### Prerequisites
- Docker and Docker Compose

### Running the Project
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/py-job-platform.git
   cd py-job-platform
   ```

2. **Start the platform:**
   ```bash
   docker-compose up --build
   ```

3. **Access the API Documentation:**
   Open your browser and navigate to `http://localhost:8000/docs` to see the interactive Swagger UI.

### Authentication
The API is protected. Use the following credentials in the "Authorize" button in Swagger:
- **Value:** `supersecretkey`

---

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Task Queue**: [Arq](https://github.com/samuelcolvin/arq) (Redis)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Containerization**: [Docker](https://www.docker.com/)

---

## Testing

The project includes both automated and manual testing guidelines. See [TESTING.md](./TESTING.md) for detailed instructions on how to verify the platform.

---

## Key Learning Points

- **Asynchronous Programming**: Extensive use of `async`/`await` across the stack.
- **Dependency Injection**: Using FastAPI's `Depends` for database sessions and security.
- **Repository Pattern**: Separating database logic from business logic.
- **Container Orchestration**: Coordinating multiple services (API, Worker, DB, Cache) with Docker.
- **Error Handling**: Robust retry mechanisms and status tracking for background tasks.
