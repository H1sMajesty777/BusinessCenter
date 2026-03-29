from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OfficeViewCreate(BaseModel):
    """
    Модель для создания записи о просмотре офиса
    
    """
    office_id: int
    duration_seconds: Optional[int] = None
    is_contacted: bool = False


class OfficeViewResponse(BaseModel):
    """
    Модель для ответа с данными о просмотре офиса
    
    Attributes:
        id: ID записи о просмотре
        user_id: ID пользователя который смотрел офис
        user_login: Логин пользователя (из JOIN с users)
        office_id: ID просмотренного офиса
        office_number: Номер офиса (из JOIN с offices)
        viewed_at: Дата и время просмотра
        duration_seconds: Длительность просмотра в секундах
        is_contacted: Связался ли пользователь после просмотра
    """
    id: int
    user_id: Optional[int]
    user_login: Optional[str] = None
    office_id: int
    office_number: Optional[str] = None
    viewed_at: datetime
    duration_seconds: Optional[int]
    is_contacted: bool