from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogCreate(BaseModel):
    """
    Модель для создания записи в журнале аудита
    
    """
    user_id: Optional[int] = None
    action_type: str
    table_name: str
    record_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None


class AuditLogResponse(BaseModel):
    """
    Модель для ответа с данными записи журнала аудита
    
    Attributes:
        id: ID записи в журнале
        user_id: ID пользователя кто совершил действие
        user_login: Логин пользователя (из JOIN с users)
        action_type: Тип действия
        table_name: Имя таблицы
        record_id: ID изменённой записи
        old_values: Старые значения (JSON)
        new_values: Новые значения (JSON)
        created_at: Время создания записи
    """
    id: int
    user_id: Optional[int]
    user_login: Optional[str] = None
    action_type: str
    table_name: str
    record_id: Optional[int]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    created_at: datetime