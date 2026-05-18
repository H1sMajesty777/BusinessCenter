import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useFavorites } from '../contexts/FavoritesContext';
import { 
  MapPin, Ruler, DollarSign, Eye, Heart, 
  TrendingUp, TrendingDown, Minus, Users, ChevronRight,
  Sparkles, Building2, ChevronLeft, ChevronRight as ChevronRightIcon
} from 'lucide-react';
import '../styles/officeCard.css';

const OfficeCard = ({ office }) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { favorites, toggleFavorite } = useFavorites();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  if (!office || !office.id) return null;
  
  const isFav = favorites.some(f => f.office_id === office.id || f.id === office.id);
  const pricePerSqm = office.area_sqm ? Math.round(office.price_per_month / office.area_sqm) : 0;
  const isClient = user?.role_id === 3;
  const isManagerOrAdmin = user?.role_id === 1 || user?.role_id === 2;
  
  const viewsCount = office.views_30d || office.views_count || 0;
  const applicationsCount = office.applications_count || 0;
  const mlProbability = office.ml_probability || null;
  
  const images = office.images || [];
  const hasImages = images.length > 0;
  
  // Автоплей каждые 4 секунды с анимацией
  useEffect(() => {
    if (!hasImages || images.length <= 1) return;
    
    if (!isHovered) {
      const interval = setInterval(() => {
        setIsTransitioning(true);
        setTimeout(() => {
          setCurrentImageIndex((prev) => (prev + 1) % images.length);
          setTimeout(() => setIsTransitioning(false), 50);
        }, 150);
      }, 4000);
      return () => clearInterval(interval);
    }
  }, [hasImages, images.length, isHovered]);
  
  const nextImage = (e) => {
    e.stopPropagation();
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentImageIndex((prev) => (prev + 1) % images.length);
      setTimeout(() => setIsTransitioning(false), 50);
    }, 150);
  };
  
  const prevImage = (e) => {
    e.stopPropagation();
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
      setTimeout(() => setIsTransitioning(false), 50);
    }, 150);
  };
  
  const goToSlide = (index, e) => {
    e.stopPropagation();
    if (index === currentImageIndex) return;
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentImageIndex(index);
      setTimeout(() => setIsTransitioning(false), 50);
    }, 150);
  };
  
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
    <div 
      className="office-card" 
      onClick={handleCardClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {isManagerOrAdmin && mlProbability && (
        <div className="office-card-ai-badge">
          <Sparkles size={12} />
          <span>AI {Math.round(mlProbability * 100)}%</span>
        </div>
      )}
      
      <div className="office-card-image">
        {hasImages ? (
          <>
            <div className="image-slider-container">
              {images.map((img, idx) => (
                <div 
                  key={img.id}
                  className={`image-slide ${idx === currentImageIndex ? 'active' : ''} ${isTransitioning ? 'transitioning' : ''}`}
                >
                  <img 
                    src={`http://localhost:8000${img.image_url}`}
                    alt={`Офис ${office.office_number}`}
                    className="office-card-img"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 24 24" fill="none" stroke="%2394a3b8" stroke-width="1"%3E%3Crect x="2" y="2" width="20" height="20" rx="2"%3E%3C/rect%3E%3Ccircle cx="8.5" cy="8.5" r="2.5"%3E%3C/circle%3E%3Cpath d="M21 15l-5-4-3 3-4-4-5 5"%3E%3C/path%3E%3C/svg%3E';
                    }}
                  />
                </div>
              ))}
            </div>
            {images.length > 1 && (
              <>
                <button className="slider-arrow-prev" onClick={prevImage}>
                  <ChevronLeft size={20} />
                </button>
                <button className="slider-arrow-next" onClick={nextImage}>
                  <ChevronRightIcon size={20} />
                </button>
                <div className="slider-dots">
                  {images.map((_, idx) => (
                    <span 
                      key={idx} 
                      className={`dot ${idx === currentImageIndex ? 'active' : ''}`}
                      onClick={(e) => goToSlide(idx, e)}
                    />
                  ))}
                </div>
              </>
            )}
          </>
        ) : (
          <div className="image-placeholder">
            <Building2 size={48} />
            <span>Нет фото</span>
          </div>
        )}
        
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
              <div className="forecast-fill" style={{ width: `${mlProbability * 100}%` }} />
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