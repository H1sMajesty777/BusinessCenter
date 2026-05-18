# backend/api/models/office_image.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OfficeImageBase(BaseModel):
    image_url: str
    file_name: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0

class OfficeImageCreate(OfficeImageBase):
    office_id: int

class OfficeImageUpdate(BaseModel):
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = None

class OfficeImageResponse(OfficeImageBase):
    id: int
    office_id: int
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True