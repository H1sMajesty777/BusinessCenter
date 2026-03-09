from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class User(BaseModel):
    id: int
    login: str
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role_id: int
    created_at: datetime
    is_active: bool


class UserCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role_id: int = 3
    is_active: bool = True 