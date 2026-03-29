from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class PaymentCreate(BaseModel):
    """
    Модель для создания платежа
    
    """
    contract_id: int
    amount: float
    payment_date: Optional[date] = None
    status_id: int = 9  # 9 = paid (оплачено)
    transaction_id: Optional[str] = None


class PaymentUpdate(BaseModel):
    """
    Модель для обновления платежа
    
    """
    amount: Optional[float] = None
    payment_date: Optional[date] = None
    status_id: Optional[int] = None
    transaction_id: Optional[str] = None


class PaymentResponse(BaseModel):
    """
    Модель для ответа с данными платежа
    
    """
    id: int
    contract_id: int
    user_id: Optional[int] = None
    user_login: Optional[str] = None
    amount: float
    payment_date: date
    status_id: int
    status_name: Optional[str] = None
    transaction_id: Optional[str] = None
    created_at: Optional[datetime] = None