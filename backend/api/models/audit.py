from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AuditLogCreate(BaseModel):
    user_id: Optional[int] = None
    action_type: str
    table_name: str
    record_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None

class AuditLog(BaseModel):
    id: int
    user_id: Optional[int]
    action_type: str
    table_name: str
    record_id: Optional[int]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    created_at: datetime