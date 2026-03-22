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
    status_id: int = 4

class Contract(BaseModel):
    id: int
    application_id: int
    user_id: int
    office_id: int
    start_date: date
    end_date: date
    total_amount: float
    status_id: int
    signed_at: datetime