// frontend/src/components/OfficeCard.jsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useFavorites } from '../contexts/FavoritesContext';
import { 
  MapPin, Ruler, DollarSign, Eye, Heart, 
  TrendingUp, TrendingDown, Minus, Users, ChevronRight,
  Sparkles
} from 'lucide-react';
import ImageSlider from './ImageSlider';
import { getOfficeImages } from '../utils/mockImages';
import '../styles/officeCard.css';

const OfficeCard = ({ office }) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { favorites, toggleFavorite } = useFavorites();
  
  if (!office || !office.id) return null;
  
  const isFav = favorites.some(f => f.office_id === office.id || f.id === office.id);
  const images = getOfficeImages(office.id);
  const pricePerSqm = office.area_sqm ? Math.round(office.price_per_month / office.area_sqm) : 0;
  const isClient = user?.role_id === 3;
  const isManagerOrAdmin = user?.role_id === 1 || user?.role_id === 2;
  
  // Реальные данные из БД (без моков!)
  const viewsCount = office.views_30d || office.views_count || 0;
  const applicationsCount = office.applications_count || 0;
  const mlProbability = office.ml_probability || null;
  
  // Расчет спроса на основе реальных просмотров
  const getDemandStatus = () => {
    if (viewsCount > 30) return { label: 'Очень высокий', color: '#22c55e', icon: TrendingUp };
    if (viewsCount > 15) return { label: 'Высокий', color: '#3b82f6', icon: TrendingUp };
    if (viewsCount > 5) return { label: 'Средний', color: '#eab308', icon: Minus };
    return { label: 'Низкий', color: '#ef4444', icon: TrendingDown };
  };
  
  const demand = getDemandStatus();
  const DemandIcon = demand.icon;

  const handleCardClick = () => navigate(`/office/${office.id}`);
  
  const handleFavoriteClick = async (e) => {
    e.stopPropagation();
    await toggleFavorite(office);
  };

  return (
    <div className="office-card" onClick={handleCardClick}>
      {/* AI-бейдж — ТОЛЬКО ДЛЯ МЕНЕДЖЕРОВ И АДМИНОВ (если есть данные) */}
      {isManagerOrAdmin && mlProbability && (
        <div className="office-card-ai-badge">
          <Sparkles size={12} />
          <span>AI {Math.round(mlProbability * 100)}%</span>
        </div>
      )}
      
      <div className="office-card-image">
        <ImageSlider images={images} officeNumber={office.office_number} />
        <button 
          className={`office-card-favorite ${isFav ? 'active' : ''}`}
          onClick={handleFavoriteClick}
        >
          <Heart size={18} />
        </button>
      </div>
      
      <div className="office-card-content">
        <div className="office-card-header">
          <div>
            <h3 className="office-card-title">Офис {office.office_number}</h3>
            <div className="office-card-location">
              <MapPin size={14} />
              <span>{office.floor} этаж</span>
            </div>
          </div>
          <div className={`office-card-status ${office.is_free ? 'free' : 'rented'}`}>
            {office.is_free ? 'Свободен' : 'Арендован'}
          </div>
        </div>
        
        <div className="office-card-specs">
          <div className="spec-item">
            <Ruler size={16} />
            <span>{office.area_sqm} м²</span>
          </div>
          <div className="spec-item">
            <DollarSign size={16} />
            <span>{pricePerSqm.toLocaleString()} ₽/м²</span>
          </div>
          <div className="spec-item price">
            <span className="price-value">{office.price_per_month.toLocaleString()} ₽</span>
            <span className="price-period">/мес</span>
          </div>
        </div>
        
        <div className="office-card-metrics">
          <div className="metric">
            <Eye size={14} />
            <span className="metric-value">{viewsCount}</span>
            <span className="metric-label">просм.</span>
          </div>
          <div className="metric">
            <Users size={14} />
            <span className="metric-value">{applicationsCount}</span>
            <span className="metric-label">заявок</span>
          </div>
          <div className="metric demand">
            <DemandIcon size={14} style={{ color: demand.color }} />
            <span className="metric-value" style={{ color: demand.color }}>{demand.label}</span>
            <span className="metric-label">спрос</span>
          </div>
        </div>
        
        {/* AI-прогноз — ТОЛЬКО ДЛЯ МЕНЕДЖЕРОВ И АДМИНОВ (если есть данные) */}
        {isManagerOrAdmin && mlProbability && (
          <div className="office-card-forecast">
            <div className="forecast-header">
              <span className="forecast-label">
                <Sparkles size={12} />
                Вероятность аренды
              </span>
              <span className="forecast-value">{Math.round(mlProbability * 100)}%</span>
            </div>
            <div className="forecast-bar">
              <div 
                className="forecast-fill" 
                style={{ width: `${mlProbability * 100}%` }}
              />
            </div>
          </div>
        )}
        
        <button className="office-card-button">
          Подробнее
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
};

export default OfficeCard;