# backend/api/models/__init__.py - исправленная версия

from .user import UserCreate, UserUpdate, UserResponse, UserLogin, Token, TokenRefresh
from .office_image import OfficeImageCreate, OfficeImageUpdate, OfficeImageResponse
from .application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from .contract import ContractCreate, ContractResponse
from .payment import PaymentCreate, PaymentUpdate, PaymentResponse
from .office_view import OfficeViewCreate, OfficeViewResponse
from .audit import AuditLogCreate, AuditLogResponse
from .favorite import FavoriteCreate, FavoriteResponse

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# ============================================
# МОДЕЛЬ OFFICE (ТОЛЬКО ОДИН РАЗ!)
# ============================================

class OfficeCreate(BaseModel):
    office_number: str = Field(..., min_length=1, max_length=20, description="Номер офиса")
    floor: int = Field(..., ge=1, le=50, description="Этаж")
    area_sqm: float = Field(..., gt=0, description="Площадь в м²")
    price_per_month: float = Field(..., gt=0, description="Цена в месяц в ₽")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    amenities: Optional[Dict[str, Any]] = Field(None, description="Удобства (JSON)")
    is_free: bool = Field(default=True, description="Свободен ли офис")

class OfficeUpdate(BaseModel):
    office_number: Optional[str] = Field(None, min_length=1, max_length=20)
    floor: Optional[int] = Field(None, ge=1, le=50)
    area_sqm: Optional[float] = Field(None, gt=0)
    price_per_month: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    amenities: Optional[Dict[str, Any]] = Field(None)
    is_free: Optional[bool] = Field(None)

# ============================================
# ЭКСПОРТ ВСЕХ МОДЕЛЕЙ
# ============================================

__all__ = [
    'UserCreate', 'UserUpdate', 'UserResponse', 'UserLogin', 'Token', 'TokenRefresh',
    'OfficeCreate', 'OfficeUpdate', 'OfficeResponse',
    'OfficeImageCreate', 'OfficeImageUpdate', 'OfficeImageResponse',
    'ApplicationCreate', 'ApplicationUpdate', 'ApplicationResponse',
    'ContractCreate', 'ContractResponse',
    'PaymentCreate', 'PaymentUpdate', 'PaymentResponse',
    'OfficeViewCreate', 'OfficeViewResponse',
    'AuditLogCreate', 'AuditLogResponse',
    'FavoriteCreate', 'FavoriteResponse'
]