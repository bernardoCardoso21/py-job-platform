from fastapi import FastAPI, Depends
from app.api.deps import verify_api_key
from app.logger import setup_logging, logger

setup_logging()

app = FastAPI(title="Async Job Platform")

@app.get("/health", dependencies=[Depends(verify_api_key)])
async def health_check():
    logger.info("health_check_called")
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Welcome to Async Job Platform API"}
