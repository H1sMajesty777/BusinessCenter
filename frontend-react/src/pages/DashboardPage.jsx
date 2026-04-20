import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useFavorites } from '../contexts/FavoritesContext';
import { getOffices } from '../services/officesService';
import { getOfficeImages } from '../utils/mockImages';
import ImageSlider from '../components/ImageSlider';
import { MapPin, Ruler, DollarSign, Eye, Heart, Search, RotateCcw } from 'lucide-react';
import '../styles/dashboard.css';
import '../styles/imageSlider.css';

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isFavorite, toggleFavorite } = useFavorites();
  const [offices, setOffices] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [tempFilters, setTempFilters] = useState({
    floor: '',
    minPrice: '',
    maxPrice: '',
    is_free: ''
  });
  
  const [activeFilters, setActiveFilters] = useState({
    floor: '',
    minPrice: '',
    maxPrice: '',
    is_free: ''
  });

  useEffect(() => {
    loadOffices();
  }, [activeFilters]);

  const loadOffices = async () => {
    setLoading(true);
    try {
      const params = {};
      if (activeFilters.floor) params.floor = parseInt(activeFilters.floor);
      if (activeFilters.minPrice) params.min_price = parseFloat(activeFilters.minPrice);
      if (activeFilters.maxPrice) params.max_price = parseFloat(activeFilters.maxPrice);
      if (activeFilters.is_free !== '') params.is_free = activeFilters.is_free === 'true';
      
      const data = await getOffices(params);
      setOffices(data);
    } catch (error) {
      console.error('Ошибка загрузки офисов:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    setActiveFilters({ ...tempFilters });
  };

  const resetFilters = () => {
    const emptyFilters = { floor: '', minPrice: '', maxPrice: '', is_free: '' };
    setTempFilters(emptyFilters);
    setActiveFilters(emptyFilters);
  };

  const handleFilterChange = (key, value) => {
    setTempFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleOfficeClick = (id) => {
    navigate(`/office/${id}`);
  };

  const handleFavoriteClick = (office, e) => {
    e.stopPropagation();
    toggleFavorite(office);
  };

  if (loading) {
    return <div className="loading-state">Загрузка офисов...</div>;
  }

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">Найдите идеальный офис</h1>
      
      <div className="filters-section">
        <div className="filters-grid">
          <div className="filter-group">
            <label className="filter-label">Этаж</label>
            <input
              type="number"
              className="filter-input"
              value={tempFilters.floor}
              onChange={(e) => handleFilterChange('floor', e.target.value)}
              placeholder="Любой"
              min="1"
              max="20"
            />
          </div>
          
          <div className="filter-group">
            <label className="filter-label">Цена (₽/мес)</label>
            <div className="filter-range">
              <input
                type="number"
                className="filter-input"
                value={tempFilters.minPrice}
                onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                placeholder="от"
                min="0"
              />
              <span>—</span>
              <input
                type="number"
                className="filter-input"
                value={tempFilters.maxPrice}
                onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                placeholder="до"
                min="0"
              />
            </div>
          </div>
          
          <div className="filter-group">
            <label className="filter-label">Статус</label>
            <select
              className="filter-select"
              value={tempFilters.is_free}
              onChange={(e) => handleFilterChange('is_free', e.target.value)}
            >
              <option value="">Все</option>
              <option value="true">Только свободные</option>
              <option value="false">Только занятые</option>
            </select>
          </div>
          
          <div className="filter-buttons">
            <button className="apply-btn" onClick={applyFilters}>
              <Search size={16} style={{ marginRight: '6px' }} />
              Применить
            </button>
            <button className="reset-btn" onClick={resetFilters}>
              <RotateCcw size={16} style={{ marginRight: '6px' }} />
              Сбросить
            </button>
          </div>
        </div>
      </div>
      
      {offices.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">Нет офисов</div>
          <div className="empty-text">Нет офисов, соответствующих критериям</div>
        </div>
      ) : (
        <div className="offices-grid">
          {offices.map(office => {
            const images = getOfficeImages(office.id);
            const isFav = isFavorite(office.id);
            
            return (
              <div 
                key={office.id} 
                className="office-card"
                onClick={() => handleOfficeClick(office.id)}
              >
                <ImageSlider 
                  images={images} 
                  officeNumber={office.office_number}
                  className="medium"
                />
                
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
                      <div className="detail-value">{office.area_sqm} <small>м²</small></div>
                    </div>
                    <div className="detail-item">
                      <DollarSign size={16} />
                      <div className="detail-label">Ставка</div>
                      <div className="detail-value">{office.price_per_month.toLocaleString()} <small>₽/мес</small></div>
                    </div>
                  </div>
                  
                  <div className={`status-badge ${office.is_free ? 'status-free' : 'status-occupied'}`}>
                    {office.is_free ? 'Свободен' : 'Занят'}
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
                      className={`favorite-btn ${isFav ? 'active' : ''}`}
                      onClick={(e) => handleFavoriteClick(office, e)}
                    >
                      <Heart size={16} style={{ marginRight: '6px' }} />
                      {isFav ? 'В избранном' : 'В избранное'}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DashboardPage;