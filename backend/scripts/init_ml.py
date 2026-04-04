# scripts/init_ml.py
"""
Скрипт для инициализации ML модуля при старте приложения
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Получение соединения с БД"""
    from api.database import get_db
    return get_db()


def init_ml_module(force_retrain: bool = False):
    """
    Инициализация ML модуля
    
    Args:
        force_retrain: Принудительное переобучение модели
    """
    logger.info("=" * 60)
    logger.info("🚀 INITIALIZING ML MODULE")
    logger.info("=" * 60)
    
    try:
        from api.ml_models import production_predictor, data_validator, config
        from api.ml_models.feature_extractor import feature_extractor
    except ImportError as e:
        logger.error(f"Failed to import ML modules: {e}")
        logger.error("Make sure the ml_models package is properly installed")
        return
    
    # Проверяем директории
    logger.info(f"📁 Model directory: {config.MODEL_DIR}")
    logger.info(f"📁 Cache directory: {config.CACHE_DIR}")
    logger.info(f"📁 Log directory: {config.LOG_DIR}")
    
    conn = None
    try:
        conn = get_db_connection()
        
        # 1. Проверяем данные
        logger.info("📊 Validating data...")
        df = feature_extractor.extract_features(conn)
        
        if len(df) == 0:
            logger.error("❌ No data found in database!")
            logger.info("Please run: docker exec -it business_center_api python /app/generate_advanced_data.py")
            return
        
        # Добавляем целевую переменную для валидации
        cursor = conn.cursor()
        target = []
        for office_id in df['office_id']:
            cursor.execute("""
                SELECT COUNT(*) FROM contracts 
                WHERE office_id = %s 
                AND signed_at > NOW() - INTERVAL '3 months'
            """, (int(office_id),))
            count = cursor.fetchone()
            # Обработка случая, когда count - это кортеж или словарь
            if isinstance(count, tuple):
                count = count[0]
            elif isinstance(count, dict):
                count = list(count.values())[0] if count else 0
            target.append(1 if count > 0 else 0)
        cursor.close()
        
        df['target'] = target
        
        report = data_validator.validate_features(df, is_training=True)
        
        if report.is_valid:
            logger.info("✅ Data validation passed")
            logger.info(f"   Samples: {report.statistics.get('dataset_size', 0)}")
            logger.info(f"   Features: {report.statistics.get('feature_count', 0)}")
            logger.info(f"   Positive ratio: {report.statistics.get('positive_ratio', 0):.2%}")
        else:
            logger.error(f"❌ Data validation failed: {report.errors}")
            if force_retrain:
                logger.warning("Force retrain enabled, continuing anyway...")
            else:
                logger.info("Use --force to retrain anyway")
                return
        
        # 2. Проверяем/обучаем модель
        if production_predictor.is_trained and not force_retrain:
            logger.info("✅ Model already loaded")
            info = production_predictor.get_model_info()
            metadata = info.get('metadata', {})
            logger.info(f"   Version: {metadata.get('version', 'unknown')}")
            logger.info(f"   AUC: {metadata.get('metrics', {}).get('roc_auc', 0):.3f}")
            logger.info(f"   Samples: {metadata.get('samples_count', 0)}")
        else:
            logger.info("🔄 Training new model...")
            result = production_predictor.train(conn, force_retrain=force_retrain)
            
            if result.get('status') == 'success':
                logger.info("✅ Model training completed!")
                metrics = result.get('metrics', {})
                logger.info(f"   AUC: {metrics.get('roc_auc', 0):.3f}")
                logger.info(f"   Accuracy: {metrics.get('accuracy', 0):.3f}")
                logger.info(f"   Samples: {result.get('metadata', {}).get('samples_count', 0)}")
            else:
                logger.error(f"❌ Training failed: {result.get('error', 'Unknown error')}")
        
        # 3. Выводим информацию о кэше
        info = production_predictor.get_model_info()
        logger.info(f"📦 Cache size: {info.get('cache_size', 0)} predictions")
        
        logger.info("=" * 60)
        logger.info("✅ ML MODULE INITIALIZED")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to initialize ML module: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


def validate_data_only():
    """Только валидация данных"""
    logger.info("=" * 60)
    logger.info("📊 DATA VALIDATION ONLY")
    logger.info("=" * 60)
    
    try:
        from api.ml_models import data_validator, config
        from api.ml_models.feature_extractor import feature_extractor
    except ImportError as e:
        logger.error(f"Failed to import ML modules: {e}")
        return
    
    conn = None
    try:
        conn = get_db_connection()
        
        df = feature_extractor.extract_features(conn)
        
        if len(df) == 0:
            logger.error("❌ No data found in database!")
            return
        
        # Добавляем целевую переменную
        cursor = conn.cursor()
        target = []
        for office_id in df['office_id']:
            cursor.execute("""
                SELECT COUNT(*) FROM contracts 
                WHERE office_id = %s 
                AND signed_at > NOW() - INTERVAL '3 months'
            """, (int(office_id),))
            count = cursor.fetchone()
            if isinstance(count, tuple):
                count = count[0]
            elif isinstance(count, dict):
                count = list(count.values())[0] if count else 0
            target.append(1 if count > 0 else 0)
        cursor.close()
        
        df['target'] = target
        
        report = data_validator.validate_features(df, is_training=True)
        
        print("\n" + "=" * 60)
        print("📊 DATA VALIDATION REPORT")
        print("=" * 60)
        print(f"Valid: {report.is_valid}")
        print(f"Samples: {report.statistics.get('dataset_size', 0)}")
        print(f"Features: {report.statistics.get('feature_count', 0)}")
        print(f"Positive ratio: {report.statistics.get('positive_ratio', 0):.2%}")
        
        if report.statistics.get('target_distribution'):
            print(f"Target distribution: {report.statistics['target_distribution']}")
        
        if report.errors:
            print(f"\n❌ Errors: {report.errors}")
        if report.warnings:
            print(f"\n⚠️ Warnings: {report.warnings}")
        if report.recommendations:
            print(f"\n💡 Recommendations: {report.recommendations}")
        
        return report
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()


def show_model_info():
    """Показать информацию о текущей модели"""
    logger.info("=" * 60)
    logger.info("📊 MODEL INFORMATION")
    logger.info("=" * 60)
    
    try:
        from api.ml_models import production_predictor, config
    except ImportError as e:
        logger.error(f"Failed to import ML modules: {e}")
        return
    
    info = production_predictor.get_model_info()
    
    if info.get('is_trained'):
        metadata = info.get('metadata', {})
        print(f"\n✅ Model is trained")
        print(f"   Version: {metadata.get('version', 'unknown')}")
        print(f"   Trained at: {metadata.get('trained_at', 'unknown')}")
        print(f"   Samples: {metadata.get('samples_count', 0)}")
        print(f"   Real samples: {metadata.get('real_samples', 0)}")
        print(f"   Synthetic samples: {metadata.get('synthetic_samples', 0)}")
        print(f"   Features: {metadata.get('feature_count', 0)}")
        
        metrics = metadata.get('metrics', {})
        if metrics:
            print(f"\n📈 Metrics:")
            print(f"   ROC AUC: {metrics.get('roc_auc', 0):.4f}")
            print(f"   Accuracy: {metrics.get('accuracy', 0):.4f}")
            print(f"   F1 Score: {metrics.get('f1_score', 0):.4f}")
        
        feature_importance = metadata.get('feature_importance', [])
        if feature_importance:
            print(f"\n🎯 Top 5 Feature Importance:")
            for i, f in enumerate(feature_importance[:5]):
                print(f"   {i+1}. {f.get('feature_index', 'unknown')}: {f.get('importance', 0):.4f}")
    else:
        print("\n❌ Model is NOT trained")
        print("   Run: python scripts/init_ml.py")
    
    print(f"\n📦 Cache size: {info.get('cache_size', 0)} predictions")
    print(f"📁 Model directory: {config.MODEL_DIR}")
    print(f"📁 Cache directory: {config.CACHE_DIR}")


def clear_cache():
    """Очистить кэш предсказаний"""
    logger.info("=" * 60)
    logger.info("🗑️ CLEARING PREDICTION CACHE")
    logger.info("=" * 60)
    
    try:
        from api.ml_models import production_predictor
    except ImportError as e:
        logger.error(f"Failed to import ML modules: {e}")
        return
    
    before = len(production_predictor._prediction_cache)
    production_predictor._prediction_cache.clear()
    
    logger.info(f"✅ Cache cleared: {before} entries removed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Module Initialization Script")
    parser.add_argument("--force", "-f", action="store_true", help="Force retrain model")
    parser.add_argument("--validate-only", "-v", action="store_true", help="Only validate data")
    parser.add_argument("--info", "-i", action="store_true", help="Show model information")
    parser.add_argument("--clear-cache", "-c", action="store_true", help="Clear prediction cache")
    
    args = parser.parse_args()
    
    if args.validate_only:
        validate_data_only()
    elif args.info:
        show_model_info()
    elif args.clear_cache:
        clear_cache()
    else:
        init_ml_module(force_retrain=args.force)