# backend/api/routers/office_images.py
# -*- coding: utf-8 -*-

import os
import shutil
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from typing import List, Optional
from api.database import get_db
from api.security import get_current_user
from api.models.office_image import OfficeImageResponse, OfficeImageUpdate
from api.rate_limiter import limiter, RATE_LIMITS

router = APIRouter(prefix="/api/office-images", tags=["Office Images"])

UPLOAD_DIR = "uploads/offices"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_MB = 10
MAX_TOTAL_STORAGE_MB = 200
MAX_IMAGES_PER_OFFICE = 20

def check_storage_usage() -> tuple:
    total_size = 0
    if os.path.exists(UPLOAD_DIR):
        for file in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    total_size_mb = total_size / (1024 * 1024)
    return total_size_mb, total_size_mb >= MAX_TOTAL_STORAGE_MB

def check_office_images_count(conn, office_id: int) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) as count FROM office_images WHERE office_id = %s", (office_id,))
        count = cursor.fetchone()['count']
        return count >= MAX_IMAGES_PER_OFFICE
    finally:
        cursor.close()

def require_admin_or_manager(current_user: dict):
    if current_user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Только администраторы и менеджеры")

@router.post("/upload/{office_id}", response_model=OfficeImageResponse)
@limiter.limit(RATE_LIMITS["authenticated"])
async def upload_office_image(
    request: Request,
    office_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    current_user: dict = Depends(get_current_user)
):
    require_admin_or_manager(current_user)
    
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Файл слишком большой. Максимум {MAX_FILE_SIZE_MB}MB")
    
    total_usage, is_full = check_storage_usage()
    if is_full:
        raise HTTPException(status_code=507, detail=f"Хранилище заполнено ({MAX_TOTAL_STORAGE_MB}MB)")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM offices WHERE id = %s", (office_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        if check_office_images_count(conn, office_id):
            raise HTTPException(status_code=400, detail=f"Превышен лимит изображений (максимум {MAX_IMAGES_PER_OFFICE})")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат изображения")
        
        file_name = f"office_{office_id}_{timestamp}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        cursor.execute("SELECT COALESCE(MAX(sort_order), -1) as max_order FROM office_images WHERE office_id = %s", (office_id,))
        max_order = cursor.fetchone()['max_order']
        
        if is_primary:
            cursor.execute("UPDATE office_images SET is_primary = FALSE WHERE office_id = %s", (office_id,))
        
        cursor.execute("""
            INSERT INTO office_images (office_id, image_url, file_name, file_size, mime_type, is_primary, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, office_id, image_url, file_name, file_size, mime_type, is_primary, sort_order, created_at
        """, (
            office_id,
            f"/uploads/offices/{file_name}",
            file.filename,
            file_size,
            file.content_type,
            is_primary,
            max_order + 1
        ))
        
        row = cursor.fetchone()
        conn.commit()
        
        return OfficeImageResponse(
            id=row['id'],
            office_id=row['office_id'],
            image_url=row['image_url'],
            file_name=row['file_name'],
            file_size=row['file_size'],
            mime_type=row['mime_type'],
            is_primary=row['is_primary'],
            sort_order=row['sort_order'],
            created_at=row['created_at']
        )
    finally:
        cursor.close()
        conn.close()

@router.get("/office/{office_id}", response_model=List[OfficeImageResponse])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_office_images(request: Request, office_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, office_id, image_url, file_name, file_size, mime_type, is_primary, sort_order, created_at
            FROM office_images
            WHERE office_id = %s
            ORDER BY sort_order ASC, created_at ASC
        """, (office_id,))
        rows = cursor.fetchall()
        return [
            OfficeImageResponse(
                id=r['id'],
                office_id=r['office_id'],
                image_url=r['image_url'],
                file_name=r['file_name'],
                file_size=r['file_size'],
                mime_type=r['mime_type'],
                is_primary=r['is_primary'],
                sort_order=r['sort_order'],
                created_at=r['created_at']
            )
            for r in rows
        ]
    finally:
        cursor.close()
        conn.close()

@router.put("/{image_id}", response_model=OfficeImageResponse)
@limiter.limit(RATE_LIMITS["authenticated"])
def update_image(
    request: Request,
    image_id: int,
    update_data: OfficeImageUpdate,
    current_user: dict = Depends(get_current_user)
):
    require_admin_or_manager(current_user)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT office_id, is_primary FROM office_images WHERE id = %s", (image_id,))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        
        if update_data.is_primary:
            cursor.execute("UPDATE office_images SET is_primary = FALSE WHERE office_id = %s", (current['office_id'],))
        
        updates = []
        params = []
        
        if update_data.is_primary is not None:
            updates.append("is_primary = %s")
            params.append(update_data.is_primary)
        
        if update_data.sort_order is not None:
            updates.append("sort_order = %s")
            params.append(update_data.sort_order)
        
        if updates:
            params.append(image_id)
            cursor.execute(f"""
                UPDATE office_images 
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, office_id, image_url, file_name, file_size, mime_type, is_primary, sort_order, created_at
            """, tuple(params))
            row = cursor.fetchone()
            conn.commit()
            return OfficeImageResponse(
                id=row['id'],
                office_id=row['office_id'],
                image_url=row['image_url'],
                file_name=row['file_name'],
                file_size=row['file_size'],
                mime_type=row['mime_type'],
                is_primary=row['is_primary'],
                sort_order=row['sort_order'],
                created_at=row['created_at']
            )
        else:
            return OfficeImageResponse(
                id=current['id'],
                office_id=current['office_id'],
                image_url=current['image_url'],
                file_name=current['file_name'],
                file_size=current['file_size'],
                mime_type=current['mime_type'],
                is_primary=current['is_primary'],
                sort_order=current['sort_order'],
                created_at=current['created_at']
            )
    finally:
        cursor.close()
        conn.close()

@router.delete("/{image_id}")
@limiter.limit(RATE_LIMITS["authenticated"])
def delete_image(
    request: Request,
    image_id: int,
    current_user: dict = Depends(get_current_user)
):
    require_admin_or_manager(current_user)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT image_url FROM office_images WHERE id = %s", (image_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        
        file_path = row['image_url'].replace("/uploads/", UPLOAD_DIR + "/")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        cursor.execute("DELETE FROM office_images WHERE id = %s RETURNING id", (image_id,))
        conn.commit()
        return {"message": "Изображение удалено"}
    finally:
        cursor.close()
        conn.close()