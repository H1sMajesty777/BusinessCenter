from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    login: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800

class UserCreate(BaseModel):
    login: str
    password: str
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role_id: int = 3
    is_active: bool = True

class User(BaseModel):
    id: int
    login: str
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role_id: int
    created_at: datetime
    is_active: bool