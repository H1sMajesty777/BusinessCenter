from pydantic import BaseModel
from typing import Optional, Dict

class OfficeCreate(BaseModel):
    office_number: str
    floor: int
    area_sqm: float
    price_per_month: float
    description: str
    amenities: Optional[Dict[str, bool]] = None
    status_id: int = 6

class OfficeUpdate(BaseModel):
    office_number: Optional[str] = None
    floor: Optional[int] = None
    area_sqm: Optional[float] = None
    price_per_month: Optional[float] = None
    description: Optional[str] = None
    amenities: Optional[Dict[str, bool]] = None
    status_id: Optional[int] = None

class Office(BaseModel):
    id: int
    office_number: str
    floor: int
    area_sqm: float
    price_per_month: float
    description: str
    amenities: Optional[Dict[str, bool]] = None
    status_id: int