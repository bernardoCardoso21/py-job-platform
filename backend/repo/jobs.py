from typing import Optional, Sequence
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import Job, JobStatus

class JobsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job: Job) -> Job:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: str) -> Optional[Job]:
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> Optional[Job]:
        result = await self.session.execute(select(Job).where(Job.idempotency_key == key))
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Job]:
        query = select(Job)
        if status:
            query = query.where(Job.status == status)
        if created_after:
            query = query.where(Job.created_at >= created_after)
        if created_before:
            query = query.where(Job.created_at <= created_before)
        
        query = query.order_by(Job.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, job: Job) -> Job:
        await self.session.commit()
        await self.session.refresh(job)
        return job
