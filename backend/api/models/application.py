from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApplicationCreate(BaseModel):
    """
    Модель для создания заявки
    
    """
    office_id: int
    comment: Optional[str] = None


class ApplicationUpdate(BaseModel):
    """
    Модель для обновления статуса заявки
    
    """
    status_id: int


class ApplicationResponse(BaseModel):
    """
    Модель для ответа с данными заявки

    """
    id: int
    user_id: int
    user_login: Optional[str] = None
    office_id: int
    office_number: Optional[str] = None
    status_id: int
    status_name: Optional[str] = None
    comment: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime] = None