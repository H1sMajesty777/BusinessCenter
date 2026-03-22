from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db
from api.models.payment import PaymentCreate
from typing import List, Optional
from datetime import date

router = APIRouter()

def payment_to_dict(row) -> dict:
    return {
        "id": row[0],
        "contract_id": row[1],
        "amount": float(row[2]),
        "payment_date": str(row[3]),
        "status_id": row[4],
        "transaction_id": row[5]
    }

@router.get("/api/payments", tags=["Платежи"])
def get_payments(contract_id: Optional[int] = None, status_id: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT id, contract_id, amount, payment_date, status_id, transaction_id FROM payments WHERE 1=1"
    params = []
    
    if contract_id:
        query += " AND contract_id = %s"
        params.append(contract_id)
    if status_id:
        query += " AND status_id = %s"
        params.append(status_id)
    
    query += " ORDER BY payment_date DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [payment_to_dict(r) for r in rows]

@router.get("/api/payments/{payment_id}", tags=["Платежи"])
def get_payment(payment_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, contract_id, amount, payment_date, status_id, transaction_id FROM payments WHERE id = %s", (payment_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Платеж не найден")
    
    return payment_to_dict(row)

@router.post("/api/payments", status_code=201, tags=["Платежи"])
def create_payment(payment: PaymentCreate):
    conn = get_db()
    cursor = conn.cursor()
    payment_date = payment.payment_date or date.today()
    cursor.execute(
        "INSERT INTO payments (contract_id, amount, payment_date, status_id, transaction_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (payment.contract_id, payment.amount, payment_date, payment.status_id, payment.transaction_id)
    )
    payment_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": payment_id, "message": "Платеж создан"}

@router.put("/api/payments/{payment_id}", tags=["Платежи"])
def update_payment(payment_id: int, status_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE payments SET status_id = %s WHERE id = %s RETURNING id", (status_id, payment_id))
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Платеж не найден")
    
    return {"id": row[0], "message": "Платеж обновлён"}

@router.delete("/api/payments/{payment_id}", tags=["Платежи"])
def delete_payment(payment_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payments WHERE id = %s RETURNING id", (payment_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Платеж не найден")
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"message": f"Платеж {payment_id} удалён"}