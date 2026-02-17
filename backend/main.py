from fastapi import FastAPI, Depends
from backend.api.deps import verify_api_key
from backend.api.jobs import router as jobs_router
from backend.logger import setup_logging, logger

setup_logging()

app = FastAPI(title="Async Job Platform")

app.include_router(jobs_router)

@app.get("/health", dependencies=[Depends(verify_api_key)])
async def health_check():
    logger.info("health_check_called")
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Welcome to Async Job Platform API"}
