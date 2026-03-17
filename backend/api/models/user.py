# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=8, max_length=128)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    role_id: int = Field(3, ge=1, le=10)
    is_active: bool = True

class UserUpdate(BaseModel):
    login: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    role_id: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None

class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    login: str
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role_id: int
    created_at: datetime
    is_active: bool

class LoginRequest(BaseModel):
    login: str
    password: str