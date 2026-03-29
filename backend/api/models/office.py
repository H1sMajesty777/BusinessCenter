from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# ========== ДЛЯ СОЗДАНИЯ ==========
class OfficeCreate(BaseModel):
    """Создание нового офиса"""
    office_number: str = Field(..., min_length=1, max_length=20, description="Номер офиса")
    floor: int = Field(..., ge=1, le=50, description="Этаж")
    area_sqm: float = Field(..., gt=0, description="Площадь в м²")
    price_per_month: float = Field(..., gt=0, description="Цена в месяц в ₽")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    amenities: Optional[Dict[str, Any]] = Field(None, description="Удобства (JSON)")
    is_free: bool = Field(default=True, description="Свободен ли офис")


# ========== ДЛЯ ОБНОВЛЕНИЯ ==========
class OfficeUpdate(BaseModel):
    """Обновление офиса (все поля необязательны)"""
    office_number: Optional[str] = Field(None, min_length=1, max_length=20)
    floor: Optional[int] = Field(None, ge=1, le=50)
    area_sqm: Optional[float] = Field(None, gt=0)
    price_per_month: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    amenities: Optional[Dict[str, Any]] = Field(None)
    is_free: Optional[bool] = Field(None)


# ========== ДЛЯ ОТВЕТА (RESPONSE) ==========
class OfficeResponse(BaseModel):
    """Ответ с данными офиса"""
    id: int
    office_number: str
    floor: int
    area_sqm: float
    price_per_month: float
    description: Optional[str]
    amenities: Optional[Dict[str, Any]]
    is_free: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True