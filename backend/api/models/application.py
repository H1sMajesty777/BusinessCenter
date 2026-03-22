from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ApplicationCreate(BaseModel):
    user_id: int
    office_id: int
    status_id: int = 1
    comment: Optional[str] = None

class Application(BaseModel):
    id: int
    user_id: int
    office_id: int
    status_id: int
    comment: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]