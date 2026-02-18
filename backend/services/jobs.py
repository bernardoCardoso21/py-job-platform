import uuid
from datetime import datetime, timezone
from typing import Optional
from arq import create_pool
from arq.connections import RedisSettings
from backend.core_config import settings
from backend.db.models import Job
from backend.domain.jobs import JobCreate
from backend.repo.jobs import JobsRepo
from fastapi import HTTPException

class JobsService:
    def __init__(self, repo: JobsRepo):
        self.repo = repo

    async def create_job(
        self, job_in: JobCreate, idempotency_key: Optional[str] = None
    ) -> Job:
        # Check idempotency
        if idempotency_key:
            existing_job = await self.repo.get_by_idempotency_key(idempotency_key)
            if existing_job:
                return existing_job

        # Validate run_at
        if job_in.run_at and job_in.run_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="run_at cannot be in the past")

        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            idempotency_key=idempotency_key,
            template_name=job_in.template_name,
            metadata_info=job_in.metadata_info,
            run_at=job_in.run_at,
        )
        
        created_job = await self.repo.create(job)
        
        # Enqueue task
        await self.enqueue_job_task(created_job.id, created_job.run_at)
        
        return created_job

    async def enqueue_job_task(self, job_id: str, run_at: Optional[datetime] = None):
        redis = await create_pool(RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT))
        # _defer_until expects a datetime object (naive or aware)
        await redis.enqueue_job('process_job', job_id, _defer_until=run_at)
        await redis.aclose()
