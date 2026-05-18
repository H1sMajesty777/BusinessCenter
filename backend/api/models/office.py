from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from api.models.office_image import OfficeImageResponse

class OfficeCreate(BaseModel):
    office_number: str = Field(..., min_length=1, max_length=20)
    floor: int = Field(..., ge=1, le=50)
    area_sqm: float = Field(..., gt=0)
    price_per_month: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    amenities: Optional[Dict[str, Any]] = Field(None)
    is_free: bool = Field(default=True)

class OfficeUpdate(BaseModel):
    office_number: Optional[str] = Field(None, min_length=1, max_length=20)
    floor: Optional[int] = Field(None, ge=1, le=50)
    area_sqm: Optional[float] = Field(None, gt=0)
    price_per_month: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    amenities: Optional[Dict[str, Any]] = Field(None)
    is_free: Optional[bool] = Field(None)

class OfficeResponse(BaseModel):
    id: int
    office_number: str
    floor: int
    area_sqm: float
    price_per_month: float
    description: Optional[str] = None
    amenities: Optional[Dict[str, Any]] = None
    is_free: bool
    created_at: Optional[datetime] = None
    images: List[OfficeImageResponse] = []
    views_30d: int = 0
    applications_count: int = 0
    ml_probability: Optional[float] = None
    
    class Config:
        from_attributes = True