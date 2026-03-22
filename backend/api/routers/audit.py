from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db
from api.models.audit import AuditLogCreate
from typing import List, Optional, Dict, Any

router = APIRouter()

def audit_to_dict(row) -> dict:
    return {
        "id": row[0],
        "user_id": row[1],
        "action_type": row[2],
        "table_name": row[3],
        "record_id": row[4],
        "old_values": row[5],
        "new_values": row[6],
        "created_at": str(row[7])
    }

@router.get("/api/audit", tags=["Аудит"])
def get_audit_logs(table_name: Optional[str] = None, user_id: Optional[int] = None, limit: int = 100):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT id, user_id, action_type, table_name, record_id, old_values, new_values, created_at FROM audit_log WHERE 1=1"
    params = []
    
    if table_name:
        query += " AND table_name = %s"
        params.append(table_name)
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [audit_to_dict(r) for r in rows]

@router.get("/api/audit/{log_id}", tags=["Аудит"])
def get_audit_log(log_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, action_type, table_name, record_id, old_values, new_values, created_at FROM audit_log WHERE id = %s", (log_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Запись аудита не найдена")
    
    return audit_to_dict(row)

@router.post("/api/audit", status_code=201, tags=["Аудит"])
def create_audit_log(log: AuditLogCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_log (user_id, action_type, table_name, record_id, old_values, new_values) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (log.user_id, log.action_type, log.table_name, log.record_id, log.old_values, log.new_values)
    )
    log_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": log_id, "message": "Запись аудита создана"}

@router.delete("/api/audit/{log_id}", tags=["Аудит"])
def delete_audit_log(log_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM audit_log WHERE id = %s RETURNING id", (log_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Запись аудита не найдена")
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"message": f"Запись {log_id} удалена"}