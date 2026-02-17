from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
from backend.db.models import JobStatus

class JobBase(BaseModel):
    template_name: str = Field(..., pattern="^report_v1$")
    metadata_info: Optional[Dict[str, Any]] = None
    run_at: Optional[datetime] = None

class JobCreate(JobBase):
    pass

class JobRead(JobBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: JobStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_file_path: Optional[str] = None
