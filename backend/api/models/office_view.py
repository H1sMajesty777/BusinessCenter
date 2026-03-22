from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OfficeViewCreate(BaseModel):
    user_id: Optional[int] = None
    office_id: int
    duration_seconds: Optional[int] = None
    is_contacted: bool = False

class OfficeView(BaseModel):
    id: int
    user_id: Optional[int]
    office_id: int
    viewed_at: datetime
    duration_seconds: Optional[int]
    is_contacted: bool