# backend/api/utils/storage_cleaner.py
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime, timedelta
from api.database import get_db

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads/offices"
MAX_STORAGE_MB = 200
MAX_FILE_AGE_DAYS = 90  # Удалять файлы старше 90 дней

def clean_old_files():
    """Очистка старых файлов и записей в БД"""
    if not os.path.exists(UPLOAD_DIR):
        return
    
    cutoff_date = datetime.now() - timedelta(days=MAX_FILE_AGE_DAYS)
    deleted_count = 0
    freed_space = 0
    
    conn = get_db()
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
        
    finally:
        cursor.close()
        conn.close()
    
    return deleted_count, freed_space


def check_and_clean_storage():
    """Проверка хранилища и очистка при необходимости"""
    if not os.path.exists(UPLOAD_DIR):
        return
    
    total_size = 0
    for file in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, file)
        if os.path.isfile(file_path):
            total_size += os.path.getsize(file_path)
    
    total_size_mb = total_size / (1024 * 1024)
    
    if total_size_mb > MAX_STORAGE_MB:
        logger.warning(f"Storage is {total_size_mb:.2f}MB, exceeding limit. Running cleanup...")
        clean_old_files()
        
        # Повторная проверка
        total_size = 0
        for file in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        total_size_mb = total_size / (1024 * 1024)
        
        if total_size_mb > MAX_STORAGE_MB:
            logger.error(f"Storage still exceeded after cleanup: {total_size_mb:.2f}MB")