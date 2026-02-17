from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core_config import settings

security = HTTPBearer()

async def verify_api_key(auth: HTTPAuthorizationCredentials = Security(security)):
    if auth.credentials != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return auth.credentials
