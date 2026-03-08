import psycopg
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel  # ← ЭТО БЫЛО ПРОПУЩЕНО!
from typing import Optional, Dict

app = FastAPI(title='Business Center API')

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Подключение к базе (через переменные окружения)
def get_db():
    return psycopg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5432),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'admin'),
        dbname=os.getenv('DB_NAME', 'project')
    )


def office_to_dict(row): #из БД в словарь
    return {
        'id': row[0], 
        'office_number': row[1], 
        'floor': row[2],
        'area_sqm': float(row[3]), 
        'price_per_month': float(row[4]),
        'description': row[5], 
        'amenities': row[6], 
        'status_id': row[7]
    }


@app.get('/') # прост главная страница
def root():
    return {'message': 'Business Center API', 'docs': '/docs'}


# -------  office с 47 по ...  строку -------


class OfficeCreate(BaseModel):
    office_number: str
    floor: int
    area_sqm: float
    price_per_month: float
    description: str
    amenities: Optional[Dict[str, bool]] = None
    status_id: int = 6

class OfficeUpdate(BaseModel):
    office_number: Optional[str] = None
    floor: Optional[int] = None
    area_sqm: Optional[float] = None
    price_per_month: Optional[float] = None
    description: Optional[str] = None
    amenities: Optional[Dict[str, bool]] = None
    status_id: Optional[int] = None


@app.get('/api/offices', tags=['Офисы']) # получение даннных из базы
def get_offices(floor: Optional[int] = None, max_price: Optional[float] = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM offices ORDER BY price_per_month')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [office_to_dict(r) for r in rows]


@app.post('/api/offices', status_code=201)
def create_office(office: OfficeCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO offices (office_number, floor, area_sqm, price_per_month, description, amenities, status_id) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id, office_number",
        (office.office_number, office.floor, office.area_sqm, office.price_per_month, office.description, 
         json.dumps(office.amenities) if office.amenities else None, office.status_id)
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return {'id': row[0], 'office_number': row[1], 'message': 'Офис создан'}


@app.delete('/api/offices/{office_id}')
def delete_office(office_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM offices WHERE id = %s RETURNING id', (office_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail='Офис не найден')
    conn.commit()
    cursor.close()
    conn.close()
    return {'message': f'Офис {office_id} удалён'}


