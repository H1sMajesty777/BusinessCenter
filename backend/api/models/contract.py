from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class ContractCreate(BaseModel):
    application_id: int
    user_id: int
    office_id: int
    start_date: date
    end_date: date
    total_amount: float
    monthly_amount: Optional[float] = None  # ← если не указана, берётся из офиса
    deposit_amount: Optional[float] = None
    special_conditions: Optional[str] = None


class ContractResponse(BaseModel):
    """
    Модель для ответа с данными договора
    
    Attributes:
        id: ID договора
        application_id: ID связанной заявки
        user_id: ID пользователя (арендатора)
        user_login: Логин пользователя (из JOIN с users)
        office_id: ID офиса
        office_number: Номер офиса (из JOIN с offices)
        start_date: Дата начала аренды
        end_date: Дата окончания аренды
        total_amount: Общая сумма договора
        status_id: ID статуса
        status_name: Название статуса (из JOIN с statuses)
        signed_at: Дата подписания договора
    """
    id: int
    application_id: int
    user_id: int
    user_login: Optional[str] = None
    office_id: int
    office_number: Optional[str] = None
    start_date: date
    end_date: date
    total_amount: float
    status_id: int
    status_name: Optional[str] = None
    signed_at: Optional[datetime] = None