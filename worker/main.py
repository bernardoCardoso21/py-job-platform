import csv
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from backend.core_config import settings
from backend.db.session import SessionLocal
from backend.db.models import Job, JobStatus
from backend.repo.jobs import JobsRepo
from backend.logger import logger, setup_logging
from arq.connections import RedisSettings
from arq.cron import cron

setup_logging()

async def process_job(ctx, job_id: str):
    logger.info("processing_job_started", job_id=job_id)
    
    async with SessionLocal() as session:
        repo = JobsRepo(session)
        job = await repo.get_by_id(job_id)
        
        if not job:
            logger.error("job_not_found", job_id=job_id)
            return

        try:
            # Update status to running
            job.status = JobStatus.running
            job.started_at = datetime.now(timezone.utc)
            await repo.update(job)
            
            # Simulate work / Generate CSV
            file_name = f"report_{job.id}.csv"
            file_path = os.path.join(settings.FILES_DIR, file_name)
            
            os.makedirs(settings.FILES_DIR, exist_ok=True)
            
            # Simple CSV content
            with open(file_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Job ID", "Created At", "Template"])
                writer.writerow([job.id, job.created_at.isoformat(), job.template_name])
            
            # Update status to succeeded
            job.status = JobStatus.succeeded
            job.completed_at = datetime.now(timezone.utc)
            job.result_file_path = file_path
            await repo.update(job)
            
            logger.info("processing_job_succeeded", job_id=job_id, file_path=file_path)
            
        except Exception as e:
            logger.exception("processing_job_failed", job_id=job_id, error=str(e))
            job.status = JobStatus.failed
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await repo.update(job)
            # Re-raise to trigger Arq retry if needed, 
            # but requirement says retry ONLY unexpected runtime exceptions
            # Arq retries based on max_retries in Worker class
            raise e

async def cleanup_old_jobs(ctx):
    logger.info("cleanup_old_jobs_started")
    retention_days = 30
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    async with SessionLocal() as session:
        # 1. Find jobs to delete to also remove their files
        result = await session.execute(
            select(Job).where(Job.created_at < cutoff_date)
        )
        jobs_to_delete = result.scalars().all()
        
        deleted_count = 0
        for job in jobs_to_delete:
            if job.result_file_path and os.path.exists(job.result_file_path):
                try:
                    os.remove(job.result_file_path)
                    logger.info("cleanup_file_deleted", job_id=job.id, file_path=job.result_file_path)
                except Exception as e:
                    logger.error("cleanup_file_failed", job_id=job.id, error=str(e))
            
            await session.delete(job)
            deleted_count += 1
            
        await session.commit()
        logger.info("cleanup_old_jobs_finished", deleted_jobs_count=deleted_count)

class WorkerSettings:
    functions = [process_job, cleanup_old_jobs]
    cron_jobs = [
        cron(cleanup_old_jobs, hour=3, minute=0) # Daily at 3 AM
    ]
    redis_settings = RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    # retries: max attempts: 3. Arq max_retries is attempts - 1.
    max_retries = 2 
    # backoff: 5s, 30s, 2m
    @staticmethod
    def retry_delay(retry_count):
        delays = [5, 30, 120]
        if retry_count < len(delays):
            return delays[retry_count]
        return delays[-1]
