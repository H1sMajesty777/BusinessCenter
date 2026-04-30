# backend/api/models/favorite.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FavoriteCreate(BaseModel):
    """Модель для добавления в избранное"""
    office_id: int


class FavoriteResponse(BaseModel):
    """Модель для ответа с данными избранного"""
    id: int
    user_id: int
    office_id: int
    office_number: Optional[str] = None
    floor: Optional[int] = None
    area_sqm: Optional[float] = None
    price_per_month: Optional[float] = None
    created_at: datetime