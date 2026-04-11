# backend/api/ml_models/feature_extractor.py
"""
Эффективный экстрактор признаков с кэшированием - УПРОЩЕННАЯ ВЕРСИЯ
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import hashlib

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Извлечение признаков для ML модели - упрощенная версия
    """
    
    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self._cache = {}
    
    def _get_cache_key(self, office_ids: Optional[List[int]] = None) -> str:
        """Генерация ключа кэша"""
        if office_ids:
            ids_str = ','.join(map(str, sorted(office_ids)))
        else:
            ids_str = 'all'
        return hashlib.md5(f"features_{ids_str}".encode()).hexdigest()
    
    def extract_features(self, conn, office_ids: Optional[List[int]] = None, 
                        use_cache: bool = True) -> pd.DataFrame:
        """
        Извлечение признаков для всех или указанных офисов
        """
        cache_key = self._get_cache_key(office_ids)
        
        # Проверяем кэш
        if use_cache and cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                logger.info(f"Using cached features for {cache_key}")
                return cached_data.copy()
        
        logger.info(f"Extracting features for {office_ids if office_ids else 'all offices'}")
        
        cursor = conn.cursor()
        
        # Упрощенный запрос - без сложных оконных функций
        query = """
        WITH 
        -- 1. Статистика просмотров
        views_stats AS (
            SELECT 
                office_id,
                COUNT(*) as total_views,
                COUNT(DISTINCT user_id) as unique_viewers,
                COALESCE(AVG(duration_seconds), 0) as avg_view_duration,
                COALESCE(SUM(CASE WHEN is_contacted THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0), 0) as contact_rate,
                COUNT(CASE WHEN viewed_at > NOW() - INTERVAL '7 days' THEN 1 END) as views_7d,
                COUNT(CASE WHEN viewed_at > NOW() - INTERVAL '30 days' THEN 1 END) as views_30d,
                COUNT(CASE WHEN viewed_at > NOW() - INTERVAL '90 days' THEN 1 END) as views_90d
            FROM office_views
            WHERE viewed_at > NOW() - INTERVAL '180 days'
            GROUP BY office_id
        ),
        
        -- 2. Статистика заявок (ИСПРАВЛЕНО)
        apps_stats AS (
            SELECT 
                office_id,
                COUNT(*) as total_apps,
                COUNT(CASE WHEN status_id = (SELECT id FROM statuses WHERE code = 'approved' AND group_name = 'application' LIMIT 1) THEN 1 END) as approved_apps,
                COUNT(CASE WHEN status_id = (SELECT id FROM statuses WHERE code = 'rejected' AND group_name = 'application' LIMIT 1) THEN 1 END) as rejected_apps,
                EXTRACT(DAY FROM (NOW() - MAX(created_at))) as days_since_last_app,
                COUNT(CASE WHEN status_id = (SELECT id FROM statuses WHERE code = 'approved' AND group_name = 'application' LIMIT 1) THEN 1 END)::float / NULLIF(COUNT(*), 0) as approval_rate
            FROM applications
            WHERE created_at > NOW() - INTERVAL '180 days'
            GROUP BY office_id
        ),

        -- 3. Статистика договоров (ИСПРАВЛЕНО)
        contracts_stats AS (
            SELECT 
                office_id,
                COUNT(*) as total_contracts,
                COALESCE(AVG(total_amount), 0) as avg_contract_amount,
                COUNT(CASE WHEN status_id = (SELECT id FROM statuses WHERE code = 'active' AND group_name = 'contract' LIMIT 1) THEN 1 END) as active_contracts
            FROM contracts
            WHERE signed_at > NOW() - INTERVAL '365 days'
            GROUP BY office_id
        ),
        
        -- 4. Конкуренция на этаже
        floor_competition AS (
            SELECT 
                floor,
                COUNT(*) as total_on_floor,
                AVG(price_per_month) as avg_price_on_floor,
                SUM(CASE WHEN is_free THEN 1 ELSE 0 END) as free_on_floor,
                SUM(CASE WHEN is_free THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0) as competition_ratio
            FROM offices
            GROUP BY floor
        )
        
        SELECT 
            -- Базовые характеристики
            o.id as office_id,
            o.office_number,
            o.floor,
            o.area_sqm,
            o.price_per_month,
            o.price_per_month / NULLIF(o.area_sqm, 0) as price_per_sqm,
            o.is_free::int as is_free,
            
            -- Возраст офиса (дней)
            EXTRACT(DAY FROM (NOW() - o.created_at)) as office_age_days,
            
            -- Views features
            COALESCE(vs.total_views, 0) as total_views,
            COALESCE(vs.unique_viewers, 0) as unique_viewers,
            COALESCE(vs.avg_view_duration, 0) as avg_view_duration,
            COALESCE(vs.contact_rate, 0) as contact_rate,
            COALESCE(vs.views_7d, 0) as views_7d,
            COALESCE(vs.views_30d, 0) as views_30d,
            COALESCE(vs.views_90d, 0) as views_90d,
            
            -- View тренды (рост/падение)
            CASE 
                WHEN COALESCE(vs.views_30d, 0) > 0 AND COALESCE(vs.views_90d, 0) > 0 
                THEN (vs.views_30d::float / vs.views_90d) - 1
                ELSE 0 
            END as views_trend_30_90d,
            
            -- Applications features
            COALESCE(apps.total_apps, 0) as total_apps,
            COALESCE(apps.approved_apps, 0) as approved_apps,
            COALESCE(apps.rejected_apps, 0) as rejected_apps,
            COALESCE(apps.approval_rate, 0) as approval_rate,
            COALESCE(apps.days_since_last_app, 90) as days_since_last_app,
            
            -- Contracts features
            COALESCE(ct.total_contracts, 0) as total_contracts,
            COALESCE(ct.avg_contract_amount, 0) as avg_contract_amount,
            COALESCE(ct.active_contracts, 0) as active_contracts,
            
            -- Competition features
            COALESCE(fc.competition_ratio, 1) as competition_ratio,
            COALESCE(fc.avg_price_on_floor, o.price_per_month) as avg_price_on_floor,
            o.price_per_month / NULLIF(fc.avg_price_on_floor, 0) as price_competition_ratio,
            COALESCE(fc.free_on_floor, 0) as free_on_floor,
            
            -- Композитные признаки
            -- Популярность (просмотры на день возраста)
            CASE 
                WHEN EXTRACT(DAY FROM (NOW() - o.created_at)) > 0 
                THEN COALESCE(vs.total_views, 0)::float / EXTRACT(DAY FROM (NOW() - o.created_at))
                ELSE 0 
            END as popularity_score
            
        FROM offices o
        LEFT JOIN views_stats vs ON o.id = vs.office_id
        LEFT JOIN apps_stats apps ON o.id = apps.office_id
        LEFT JOIN contracts_stats ct ON o.id = ct.office_id
        LEFT JOIN floor_competition fc ON o.floor = fc.floor
        """
        
        if office_ids:
            placeholders = ','.join(['%s'] * len(office_ids))
            query += f" WHERE o.id IN ({placeholders})"
            cursor.execute(query, office_ids)
        else:
            cursor.execute(query)
        
        # Получаем данные
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        if rows:
            df = pd.DataFrame(rows, columns=columns)
        else:
            df = pd.DataFrame(columns=columns)
        
        cursor.close()
        
        # Заменяем NULL значения
        df = df.fillna(0)
        
        # Преобразуем типы
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            df[col] = df[col].astype(float)
        
        # Логируем информацию о данных
        logger.info(f"Extracted {len(df)} rows with {len(columns)} features")
        
        # Сохраняем в кэш
        if use_cache and len(df) > 0:
            self._cache[cache_key] = (df.copy(), datetime.now())
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Получить список всех признаков"""
        return [
            'floor', 'area_sqm', 'price_per_month', 'price_per_sqm', 'is_free',
            'office_age_days', 'total_views', 'unique_viewers', 'avg_view_duration',
            'contact_rate', 'views_7d', 'views_30d', 'views_90d', 'views_trend_30_90d',
            'total_apps', 'approval_rate', 'days_since_last_app', 'total_contracts',
            'avg_contract_amount', 'active_contracts', 'competition_ratio',
            'price_competition_ratio', 'free_on_floor', 'popularity_score'
        ]


# Глобальный экземпляр
feature_extractor = FeatureExtractor()