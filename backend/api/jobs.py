import os
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import verify_api_key
from backend.db.session import get_db
from backend.db.models import JobStatus
from backend.domain.jobs import JobCreate, JobRead
from backend.repo.jobs import JobsRepo
from backend.services.jobs import JobsService
from datetime import datetime
from fastapi.responses import FileResponse

router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(verify_api_key)])

@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    repo = JobsRepo(db)
    service = JobsService(repo)
    return await service.create_job(job_in, idempotency_key=idempotency_key)

@router.get("/", response_model=List[JobRead])
async def list_jobs(
    status: Optional[JobStatus] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    repo = JobsRepo(db)
    return await repo.list_jobs(
        status=status,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )

@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    repo = JobsRepo(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/download")
async def download_job_result(job_id: str, db: AsyncSession = Depends(get_db)):
    repo = JobsRepo(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.succeeded:
        raise HTTPException(status_code=400, detail="Job result is not available yet")
    
    if not job.result_file_path or not os.path.exists(job.result_file_path):
        raise HTTPException(status_code=404, detail="Result file not found")
    
    return FileResponse(
        path=job.result_file_path,
        filename=f"report_{job.id}.csv",
        media_type="text/csv"
    )
