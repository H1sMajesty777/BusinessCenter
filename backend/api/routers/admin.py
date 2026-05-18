# backend/api/routers/admin.py
# -*- coding: utf-8 -*-
"""
Административные роуты: очистка хранилища, статистика, управление системой
Доступ: ТОЛЬКО АДМИНИСТРАТОРЫ (role_id = 1)
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends, Request, Query 
from datetime import datetime, timedelta
from typing import Optional

from api.database import get_db
from api.security import get_current_user
from api.rate_limiter import limiter, RATE_LIMITS

router = APIRouter(prefix="/api/admin", tags=["Admin"])
logger = logging.getLogger(__name__)

# Конфигурация
UPLOAD_DIR = "uploads/offices"
MAX_STORAGE_MB = 200
MAX_FILE_AGE_DAYS = 90

def require_admin(current_user: dict):
    """Проверка: только администратор"""
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")


def get_storage_usage() -> tuple:
    """Получить использование хранилища"""
    total_size = 0
    file_count = 0
    
    if os.path.exists(UPLOAD_DIR):
        for file in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
                file_count += 1
    
    total_size_mb = total_size / (1024 * 1024)
    return total_size_mb, file_count, total_size_mb >= MAX_STORAGE_MB


def clean_old_files(conn=None) -> tuple:
    """Очистка старых файлов и записей в БД"""
    if not os.path.exists(UPLOAD_DIR):
        return 0, 0
    
    cutoff_date = datetime.now() - timedelta(days=MAX_FILE_AGE_DAYS)
    deleted_count = 0
    freed_space = 0
    
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    cursor = conn.cursor()
    
    try:
        # Получаем старые изображения из БД
        cursor.execute("""
            SELECT id, image_url, created_at 
            FROM office_images 
            WHERE created_at < %s
        """, (cutoff_date,))
        
        old_images = cursor.fetchall()
        
        for img in old_images:
            # Удаляем файл
            file_path = img['image_url'].replace("/uploads/", UPLOAD_DIR + "/")
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                freed_space += file_size
                os.remove(file_path)
                deleted_count += 1
            
            # Удаляем запись из БД
            cursor.execute("DELETE FROM office_images WHERE id = %s", (img['id'],))
        
        conn.commit()
        
        if deleted_count > 0:
            logger.info(f"Cleaned {deleted_count} old images, freed {freed_space / (1024*1024):.2f} MB")
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
    finally:
        cursor.close()
        if should_close:
            conn.close()
    
    return deleted_count, freed_space


def clean_audit_log(conn=None) -> int:
    """Очистка старого аудит-лога"""
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    cursor = conn.cursor()
    deleted_count = 0
    
    try:
        # Получаем количество записей
        cursor.execute("SELECT COUNT(*) as count FROM audit_log")
        total_count = cursor.fetchone()['count']
        
        # Если больше 100 000 - удаляем старые
        if total_count > 100000:
            # Оставляем только 50 000 последних
            cursor.execute("""
                DELETE FROM audit_log 
                WHERE id NOT IN (
                    SELECT id FROM audit_log 
                    ORDER BY created_at DESC 
                    LIMIT 50000
                )
            """)
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Cleaned {deleted_count} old audit records")
        
        # Также удаляем записи старше 180 дней
        cursor.execute("""
            DELETE FROM audit_log 
            WHERE created_at < NOW() - INTERVAL '180 days'
        """)
        deleted_count += cursor.rowcount
        conn.commit()
        
    except Exception as e:
        logger.error(f"Audit cleanup error: {e}")
    finally:
        cursor.close()
        if should_close:
            conn.close()
    
    return deleted_count


# ===================================================================
# ENDPOINTS
# ===================================================================

@router.get("/storage/stats")
@limiter.limit(RATE_LIMITS["admin"])
def get_storage_stats(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Статистика хранилища изображений
    Доступ: ТОЛЬКО АДМИН
    """
    require_admin(current_user)
    
    total_usage_mb, file_count, is_full = get_storage_usage()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Статистика по офисам
        cursor.execute("""
            SELECT 
                o.office_number,
                COUNT(img.id) as images_count,
                COALESCE(SUM(img.file_size), 0) as total_size
            FROM offices o
            LEFT JOIN office_images img ON o.id = img.office_id
            GROUP BY o.id, o.office_number
            HAVING COUNT(img.id) > 0
            ORDER BY total_size DESC
            LIMIT 10
        """)
        office_stats = cursor.fetchall()
        
        # Общая статистика по БД
        cursor.execute("SELECT COUNT(*) as count FROM office_images")
        total_images = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM audit_log")
        audit_count = cursor.fetchone()['count']
        
        return {
            "storage": {
                "total_usage_mb": round(total_usage_mb, 2),
                "max_limit_mb": MAX_STORAGE_MB,
                "is_full": is_full,
                "remaining_mb": round(max(0, MAX_STORAGE_MB - total_usage_mb), 2),
                "file_count": file_count,
                "total_images_in_db": total_images
            },
            "audit": {
                "total_records": audit_count,
                "retention_days": 180
            },
            "top_offices": [
                {
                    "office_number": r['office_number'],
                    "images_count": r['images_count'],
                    "total_size_mb": round(r['total_size'] / (1024 * 1024), 2) if r['total_size'] else 0
                }
                for r in office_stats
            ]
        }
    finally:
        cursor.close()
        conn.close()


@router.post("/cleanup/images")
@limiter.limit(RATE_LIMITS["admin"])
def cleanup_images(request: Request, 
                   days: Optional[int] = Query(90, ge=1, le=365, description="Удалять файлы старше N дней"),
                   current_user: dict = Depends(get_current_user)):
    """
    Очистка старых изображений
    Доступ: ТОЛЬКО АДМИН
    """
    require_admin(current_user)
    
    global MAX_FILE_AGE_DAYS
    old_days = MAX_FILE_AGE_DAYS
    MAX_FILE_AGE_DAYS = days
    
    try:
        deleted_count, freed_space = clean_old_files()
        
        return {
            "message": f"Очистка завершена",
            "deleted_files": deleted_count,
            "freed_space_mb": round(freed_space / (1024 * 1024), 2),
            "files_older_than_days": days
        }
    finally:
        MAX_FILE_AGE_DAYS = old_days


@router.post("/cleanup/audit")
@limiter.limit(RATE_LIMITS["admin"])
def cleanup_audit(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Очистка старого аудит-лога
    Доступ: ТОЛЬКО АДМИН
    """
    require_admin(current_user)
    
    deleted_count = clean_audit_log()
    
    return {
        "message": "Очистка аудит-лога завершена",
        "deleted_records": deleted_count,
        "retained_records": 50000
    }


@router.post("/cleanup/all")
@limiter.limit(RATE_LIMITS["admin"])
def cleanup_all(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Полная очистка (изображения + аудит)
    Доступ: ТОЛЬКО АДМИН
    """
    require_admin(current_user)
    
    # Очистка изображений
    images_deleted, freed_space = clean_old_files()
    
    # Очистка аудита
    audit_deleted = clean_audit_log()
    
    return {
        "message": "Полная очистка завершена",
        "images": {
            "deleted_files": images_deleted,
            "freed_space_mb": round(freed_space / (1024 * 1024), 2)
        },
        "audit": {
            "deleted_records": audit_deleted
        }
    }


@router.get("/system/health")
@limiter.limit(RATE_LIMITS["admin"])
def system_health(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Проверка здоровья системы
    Доступ: ТОЛЬКО АДМИН
    """
    require_admin(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка БД
        cursor.execute("SELECT 1 as connected")
        db_ok = cursor.fetchone() is not None
        
        # Проверка Redis (опционально)
        redis_ok = False
        try:
            from api.database import get_redis
            redis_client = get_redis()
            redis_client.ping()
            redis_ok = True
        except:
            redis_ok = False
        
        # Статистика
        cursor.execute("SELECT COUNT(*) as count FROM users")
        users_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM offices")
        offices_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM contracts WHERE status_id = 4")
        active_contracts = cursor.fetchone()['count']
        
        total_usage_mb, _, is_full = get_storage_usage()
        
        return {
            "status": "healthy" if db_ok else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": {"status": "ok" if db_ok else "error"},
                "redis": {"status": "ok" if redis_ok else "error"},
                "storage": {
                    "status": "warning" if is_full else "ok",
                    "usage_mb": round(total_usage_mb, 2),
                    "limit_mb": MAX_STORAGE_MB
                }
            },
            "statistics": {
                "users": users_count,
                "offices": offices_count,
                "active_contracts": active_contracts
            }
        }
    finally:
        cursor.close()
        conn.close()