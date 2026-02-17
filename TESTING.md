### Testing Guideline: Async Job Platform

This guide explains how to verify and test the Async Job Platform, covering both automated and manual testing.

---

### 1. Interactive Testing (Swagger UI) - Recommended

FastAPI automatically generates an interactive API documentation. This is the easiest way to test the API without writing commands.

1.  **Open Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
2.  **Authorize:** Click the **"Authorize"** button (top right), enter `supersecretkey`, and click **Authorize**.
3.  **Try it out:**
    *   Find the `POST /jobs/` endpoint.
    *   Click **"Try it out"**.
    *   Edit the request body if needed (ensure `template_name` is `"report_v1"`).
    *   Click **Execute**.
4.  **Check Results:** You will see the response immediately in the browser.

---

### 2. Automated Testing (pytest)

The platform includes a suite of automated tests using `pytest` and `httpx`. These tests cover:
- Authentication (Authorized vs. Unauthorized access)
- Health Checks
- Job Creation & Pydantic Validation
- Idempotency-Key support

#### Running Tests via Docker (Recommended)
You can run the tests directly within the API container to ensure the environment is consistent:

```bash
docker-compose exec api pytest tests/
```

---

### 2. Manual End-to-End Testing (PowerShell)

Use these steps to verify the full job lifecycle (Creation → Processing → Polling → Download).

#### **A. Authenticated Health Check**
Verify the API is up and your API key is correct.
```powershell
$headers = @{ Authorization = "Bearer supersecretkey" }
Invoke-RestMethod -Uri "http://localhost:8000/health" -Headers $headers
```
*Expected: `{"status": "ok"}`*

#### **B. Create a Job (POST /jobs)**
Submit a job request. Note the `Idempotency-Key` which prevents duplicate jobs if the request is retried.
```powershell
$body = @{ template_name = "report_v1" } | ConvertTo-Json
$headers = @{ 
    Authorization = "Bearer supersecretkey"
    "Idempotency-Key" = "test-key-001"
}
$job = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/jobs/" -Headers $headers -Body $body -ContentType "application/json"
$job
```
*Expected: Returns a job object with `status: "queued"`. Copy the `id` for the next step.*

#### **C. Poll Job Status (GET /jobs/{id})**
Wait a few seconds for the worker to process the job, then check its status.
```powershell
$jobId = $job.id  # Or paste the ID manually
Invoke-RestMethod -Uri "http://localhost:8000/jobs/$jobId" -Headers $headers
```
*Expected: `status` should eventually transition from `queued` -> `running` -> `succeeded`.*

#### **D. List All Jobs (GET /jobs)**
Test filtering and pagination.
```powershell
# Get only succeeded jobs
Invoke-RestMethod -Uri "http://localhost:8000/jobs/?status=succeeded&limit=5" -Headers $headers
```

#### **E. Download the Result (GET /jobs/{id}/download)**
Once the status is `succeeded`, download the generated CSV file.
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/jobs/$jobId/download" -Headers $headers -OutFile "report_downloaded.csv"
```
*Verification: Open `report_downloaded.csv` to see the generated content.*

---

### 3. Monitoring Worker Logs

To see the background worker processing jobs, generating files, and handling retries/cleanup:

```bash
docker-compose logs -f worker
```

---

### 4. Data Retention Verification (Advanced)
The daily cleanup task runs automatically at 3 AM. To verify the cleanup logic manually, you would need to:
1. Manually update a job's `created_at` in the database to be > 30 days old.
2. Trigger the `cleanup_old_jobs` task in the worker (this requires using the `arq` CLI or code modification for immediate execution).
