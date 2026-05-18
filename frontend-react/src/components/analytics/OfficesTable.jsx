// frontend/src/components/analytics/OfficesTable.jsx
import React, { useState } from 'react';
import { Eye, TrendingUp, TrendingDown, Minus, Star, ChevronRight, Building2, Ruler, DollarSign, MapPin } from 'lucide-react';

const OfficesTable = ({ offices, loading, onSelectOffice }) => {
  const [hoveredRow, setHoveredRow] = useState(null);
  
  if (loading) {
    return (
      <div className="offices-table-loading">
        <div className="loading-spinner"></div>
        <p>Загрузка аналитики...</p>
      </div>
    );
  }
  
  if (!offices.length) {
    return (
      <div className="offices-table-empty">
        <div className="empty-icon">📊</div>
        <h3>Нет данных для отображения</h3>
        <p>Попробуйте изменить параметры фильтрации</p>
      </div>
    );
  }
  
  const getProbabilityIcon = (probability) => {
    if (probability >= 70) return <TrendingUp size={18} className="trend-up" />;
    if (probability >= 40) return <Minus size={18} className="trend-stable" />;
    return <TrendingDown size={18} className="trend-down" />;
  };
  
  const getProbabilityClass = (probability) => {
    if (probability >= 70) return 'high';
    if (probability >= 40) return 'medium';
    return 'low';
  };
  
  return (
    <div className="offices-table-container">
      <div className="table-header">
        <div>
          <h3 className="table-title">
            <Star size={20} className="title-icon" />
            Детальный прогноз по офисам
          </h3>
          <p className="table-subtitle">AI-анализ вероятности аренды для каждого помещения</p>
        </div>
        <div className="table-stats">
          <div className="stat-card">
            <span className="stat-value">{offices.length}</span>
            <span className="stat-label">Всего</span>
          </div>
          <div className="stat-card high">
            <span className="stat-value">{offices.filter(o => o.category === 'high').length}</span>
            <span className="stat-label">Высокий</span>
          </div>
          <div className="stat-card medium">
            <span className="stat-value">{offices.filter(o => o.category === 'medium').length}</span>
            <span className="stat-label">Средний</span>
          </div>
          <div className="stat-card low">
            <span className="stat-value">{offices.filter(o => o.category === 'low').length}</span>
            <span className="stat-label">Низкий</span>
          </div>
        </div>
      </div>
      
      <div className="offices-table-wrapper">
        <div className="offices-table">
          {offices.map(office => {
            const probabilityPercent = Math.round((office.probability || 0) * 100);
            const probClass = getProbabilityClass(probabilityPercent);
            
            return (
              <div 
                key={office.office_id}
                className={`office-card-row ${hoveredRow === office.office_id ? 'hovered' : ''}`}
                onMouseEnter={() => setHoveredRow(office.office_id)}
                onMouseLeave={() => setHoveredRow(null)}
              >
                <div className="row-main">
                  <div className="office-info">
                    <div className="office-number">
                      <Building2 size={20} />
                      <strong>Офис {office.office_number}</strong>
                    </div>
                    <div className="office-details">
                      <span className="detail">
                        <MapPin size={14} />
                        {office.floor} этаж
                      </span>
                      <span className="detail">
                        <Ruler size={14} />
                        {office.area_sqm} м²
                      </span>
                      <span className="detail price">
                        <DollarSign size={14} />
                        {office.price_per_month?.toLocaleString()} ₽/мес
                      </span>
                    </div>
                  </div>
                  
                  <div className="probability-section">
                    <div className="probability-header">
                      <span className="probability-label">Вероятность аренды</span>
                      <div className="probability-value-wrapper">
                        {getProbabilityIcon(probabilityPercent)}
                        <span className={`probability-value ${probClass}`}>
                          {probabilityPercent}%
                        </span>
                      </div>
                    </div>
                    <div className="probability-bar-container">
                      <div 
                        className={`probability-bar ${probClass}`}
                        style={{ width: `${probabilityPercent}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="category-section">
                    <span className={`category-badge ${office.category}`}>
                      {office.category === 'high' ? 'Высокий спрос' : 
                       office.category === 'medium' ? 'Средний спрос' : 'Низкий спрос'}
                    </span>
                  </div>
                  
                  <button 
                    className="view-details-btn"
                    onClick={() => onSelectOffice(office)}
                  >
                    <span>Анализ</span>
                    <ChevronRight size={18} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default OfficesTable;