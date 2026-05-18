// frontend/src/components/analytics/OfficeDetailModal.jsx
import React, { useEffect, useState } from 'react';
import { X, TrendingUp, TrendingDown, Minus, Target, Zap, DollarSign, Building2, AlertCircle, CheckCircle, Clock, Eye, FileText, CreditCard } from 'lucide-react';
import api from '../../services/api';
import { getFeatureInfo } from '../../utils/featureMapping';

const OfficeDetailModal = ({ office, onClose }) => {
  const [forecastDetails, setForecastDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const loadDetails = async () => {
      setLoading(true);
      try {
        const response = await api.get(`/ai/rental-prediction/explain/${office.office_id}`);
        setForecastDetails(response.data);
      } catch (error) {
        console.error('Ошибка загрузки деталей:', error);
      } finally {
        setLoading(false);
      }
    };
    loadDetails();
    
    // Блокируем скролл body
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [office.office_id]);
  
  const probabilityPercent = Math.round((office.probability || 0) * 100);
  
  const getProbabilityColor = () => {
    if (probabilityPercent >= 70) return '#10b981';
    if (probabilityPercent >= 40) return '#f59e0b';
    return '#ef4444';
  };
  
  const getRecommendations = () => {
    if (probabilityPercent >= 70) {
      return [
        { text: 'Высокий спрос! Ускорьте процесс оформления', type: 'success' },
        { text: 'Рассмотрите возможность повышения цены на 5-10%', type: 'warning' },
        { text: 'Свяжитесь с заинтересованными клиентами в первую очередь', type: 'info' }
      ];
    } else if (probabilityPercent >= 40) {
      return [
        { text: 'Улучшите презентацию офиса (фото, описание)', type: 'info' },
        { text: 'Добавьте виртуальный тур для привлечения внимания', type: 'info' },
        { text: 'Рассмотрите гибкие условия аренды', type: 'warning' }
      ];
    } else {
      return [
        { text: 'Рекомендуется снижение цены на 10-15%', type: 'danger' },
        { text: 'Добавьте профессиональные фото и видео', type: 'info' },
        { text: 'Активируйте рекламную кампанию', type: 'warning' },
        { text: 'Предложите специальные условия (первый месяц в подарок)', type: 'success' }
      ];
    }
  };
  
  return (
    <div className="detail-modal-overlay" onClick={onClose}>
      <div className="detail-modal" onClick={(e) => e.stopPropagation()}>
        {/* Заголовок */}
        <div className="modal-header">
          <div className="header-left">
            <div className="office-badge-large">
              <Building2 size={24} />
              <span>Офис {office.office_number}</span>
            </div>
            <div className="office-location-large">
              <span>{office.floor} этаж</span>
              <span className="separator">•</span>
              <span>{office.area_sqm} м²</span>
              <span className="separator">•</span>
              <span className="price-highlight">{office.price_per_month?.toLocaleString()} ₽/мес</span>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>
        
        {/* Основной контент */}
        <div className="modal-body">
          {/* Главная метрика */}
          <div className="main-metric">
            <div className="metric-gauge">
              <svg width="140" height="140" viewBox="0 0 140 140">
                <circle cx="70" cy="70" r="62" fill="none" stroke="#e2e8f0" strokeWidth="8"/>
                <circle 
                  cx="70" cy="70" r="62" fill="none" 
                  stroke={getProbabilityColor()} 
                  strokeWidth="8"
                  strokeDasharray={`${2 * Math.PI * 62 * probabilityPercent / 100} ${2 * Math.PI * 62}`}
                  strokeLinecap="round"
                  transform="rotate(-90 70 70)"
                  className="gauge-animation"
                />
                <text x="70" y="70" textAnchor="middle" dominantBaseline="middle" className="gauge-text">
                  {probabilityPercent}%
                </text>
              </svg>
            </div>
            <div className="metric-description">
              <h3>Вероятность аренды</h3>
              <p className={`metric-status ${probabilityPercent >= 70 ? 'high' : probabilityPercent >= 40 ? 'medium' : 'low'}`}>
                {probabilityPercent >= 70 ? '🔥 Высокий спрос' :
                 probabilityPercent >= 40 ? '📈 Средний спрос' : '⚠️ Низкий спрос'}
              </p>
            </div>
          </div>
          
          {/* Детальная статистика в виде сетки */}
          <div className="stats-grid-modern">
            <div className="stat-card-modern">
              <Eye size={20} />
              <div className="stat-content">
                <span className="stat-value">{forecastDetails?.detailed_stats?.total_views || 0}</span>
                <span className="stat-label">Просмотров</span>
              </div>
            </div>
            <div className="stat-card-modern">
              <FileText size={20} />
              <div className="stat-content">
                <span className="stat-value">{forecastDetails?.detailed_stats?.total_applications || 0}</span>
                <span className="stat-label">Заявок</span>
              </div>
            </div>
            <div className="stat-card-modern">
              <CreditCard size={20} />
              <div className="stat-content">
                <span className="stat-value">{forecastDetails?.detailed_stats?.total_contracts || 0}</span>
                <span className="stat-label">Договоров</span>
              </div>
            </div>
            <div className="stat-card-modern">
              <DollarSign size={20} />
              <div className="stat-content">
                <span className="stat-value">{forecastDetails?.detailed_stats?.price_per_sqm?.toLocaleString() || 0} ₽</span>
                <span className="stat-label">Цена за м²</span>
              </div>
            </div>
          </div>
          
          {/* Факторы влияния */}
          <div className="factors-section-modern">
            <h3 className="section-title">
              <Target size={18} />
              Ключевые факторы прогноза
            </h3>
            <div className="factors-grid-modern">
              {forecastDetails?.top_factors?.slice(0, 4).map((factor, idx) => {
                const info = getFeatureInfo(factor.feature);
                const importance = Math.round(factor.importance * 100);
                return (
                  <div key={idx} className="factor-card-modern">
                    <div className="factor-header-modern">
                      <span className="factor-name">{info.name || factor.feature}</span>
                      <span className="factor-percent">{importance}%</span>
                    </div>
                    <div className="factor-bar-modern">
                      <div className="factor-fill-modern" style={{ width: `${importance}%` }} />
                    </div>
                    <div className="factor-description">{info.description || 'Влияние на прогноз'}</div>
                  </div>
                );
              })}
            </div>
          </div>
          
          {/* Рекомендации */}
          <div className="recommendations-section-modern">
            <h3 className="section-title">
              <Zap size={18} />
              Рекомендации AI
            </h3>
            <div className="recommendations-grid-modern">
              {getRecommendations().map((rec, idx) => (
                <div key={idx} className={`recommendation-card-modern ${rec.type}`}>
                  <div className="rec-icon">
                    {rec.type === 'success' && <CheckCircle size={16} />}
                    {rec.type === 'warning' && <AlertCircle size={16} />}
                    {rec.type === 'danger' && <AlertCircle size={16} />}
                    {rec.type === 'info' && <Clock size={16} />}
                  </div>
                  <span>{rec.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Кнопки действий */}
        <div className="modal-footer-modern">
          <button className="btn-primary-modern" onClick={() => window.open(`/office/${office.office_id}`, '_blank')}>
            Перейти к офису
          </button>
          <button className="btn-secondary-modern" onClick={onClose}>
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
};

export default OfficeDetailModal;