import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useFavorites } from '../contexts/FavoritesContext';
import { Building2, Ruler, DollarSign, MapPin, Eye, Heart, Trash2 } from 'lucide-react';
import '../styles/favorites.css';

const FavoritesPage = () => {
  const navigate = useNavigate();
  const { favorites, removeFromFavorites } = useFavorites();

  const handleOfficeClick = (id) => {
    navigate(`/office/${id}`);
  };

  const handleRemove = (office, e) => {
    e.stopPropagation();
    removeFromFavorites(office.id);
  };

  if (favorites.length === 0) {
    return (
      <div className="favorites-container">
        <h1 className="favorites-title">❤️ Избранное</h1>
        <div className="empty-favorites">
          <Heart size={64} style={{ marginBottom: '20px', opacity: 0.3 }} />
          <div className="empty-title">Нет избранных офисов</div>
          <div className="empty-text">Добавляйте офисы в избранное, чтобы они появлялись здесь</div>
          <button className="go-to-catalog" onClick={() => navigate('/dashboard')}>
            Перейти к каталогу
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="favorites-container">
      <h1 className="favorites-title">
        ❤️ Избранное
        <span className="favorites-count">{favorites.length} офисов</span>
      </h1>
      
      <div className="favorites-grid">
        {favorites.map(office => (
          <div 
            key={office.id} 
            className="favorite-card"
            onClick={() => handleOfficeClick(office.id)}
          >
            <div className="office-image">
              <Building2 size={48} color="white" opacity={0.8} />
            </div>
            
            <div className="office-content">
              <div className="office-header">
                <h3 className="office-number">Офис {office.office_number}</h3>
                <span className="office-floor">
                  <MapPin size={14} style={{ marginRight: '4px' }} />
                  {office.floor} этаж
                </span>
              </div>
              
              <div className="office-details">
                <div className="detail-item">
                  <Ruler size={16} />
                  <div className="detail-label">Площадь</div>
                  <div className="detail-value">{office.area_sqm} м²</div>
                </div>
                <div className="detail-item">
                  <DollarSign size={16} />
                  <div className="detail-label">Цена</div>
                  <div className="detail-value">{office.price_per_month.toLocaleString()} ₽/мес</div>
                </div>
              </div>
              
              <div className="office-actions">
                <button 
                  className="btn-details"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOfficeClick(office.id);
                  }}
                >
                  <Eye size={16} style={{ marginRight: '6px' }} />
                  Подробнее
                </button>
                <button 
                  className="btn-remove"
                  onClick={(e) => handleRemove(office, e)}
                >
                  <Trash2 size={16} style={{ marginRight: '6px' }} />
                  Удалить
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FavoritesPage;