from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class PaymentCreate(BaseModel):
    contract_id: int
    amount: float
    payment_date: date = None
    status_id: int = 4
    transaction_id: Optional[str] = None

class Payment(BaseModel):
    id: int
    contract_id: int
    amount: float
    payment_date: date
    status_id: int
    transaction_id: Optional[str]