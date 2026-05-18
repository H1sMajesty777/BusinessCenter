// frontend/src/pages/DashboardPage.jsx

import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useFavorites } from '../contexts/FavoritesContext';
import { getOffices } from '../services/officesService';
import OfficeCard from '../components/OfficeCard';
import { Search, RotateCcw, Building2 } from 'lucide-react';
import '../styles/dashboard.css';

const DashboardPage = () => {
  const { user } = useAuth();
  const { toggleFavorite } = useFavorites();
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
      
      // ❌ УБИРАЕМ МОК-ДАННЫЕ! Используем реальные из БД
      // Если в БД нет этих полей, они будут undefined - это нормально
      const officesWithRealData = data.map(office => ({
        ...office,
        // Оставляем как есть - без поддельных данных!
        // views_30d: office.views_30d || 0,  // если есть в БД
        // applications_count: office.applications_count || 0,
        // ml_probability: office.ml_probability || null
      }));
      
      setOffices(officesWithRealData);
    } catch (error) {
      console.error('Ошибка загрузки офисов:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => setActiveFilters({ ...tempFilters });
  const resetFilters = () => {
    const empty = { floor: '', minPrice: '', maxPrice: '', is_free: '' };
    setTempFilters(empty);
    setActiveFilters(empty);
  };
  const handleFilterChange = (key, value) => setTempFilters(prev => ({ ...prev, [key]: value }));

  if (loading) {
    return (
      <div className="loading-state">
        <div className="loading-spinner"></div>
        <p>Загрузка офисов...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-hero">
        <h1 className="dashboard-title">Найдите идеальный офис</h1>
        <p className="dashboard-subtitle">{offices.length} офисов доступно для аренды</p>
      </div>

      <div className="filters-section">
        <div className="filters-grid">
          <div className="filter-group">
            <label className="filter-label">Этаж</label>
            <input type="number" className="filter-input" value={tempFilters.floor} onChange={(e) => handleFilterChange('floor', e.target.value)} placeholder="Любой" />
          </div>
          <div className="filter-group">
            <label className="filter-label">Цена (₽/мес)</label>
            <div className="filter-range">
              <input type="number" className="filter-input" value={tempFilters.minPrice} onChange={(e) => handleFilterChange('minPrice', e.target.value)} placeholder="от" />
              <span>—</span>
              <input type="number" className="filter-input" value={tempFilters.maxPrice} onChange={(e) => handleFilterChange('maxPrice', e.target.value)} placeholder="до" />
            </div>
          </div>
          <div className="filter-group">
            <label className="filter-label">Статус</label>
            <select className="filter-select" value={tempFilters.is_free} onChange={(e) => handleFilterChange('is_free', e.target.value)}>
              <option value="">Все</option>
              <option value="true">Только свободные</option>
              <option value="false">Только занятые</option>
            </select>
          </div>
          <div className="filter-buttons">
            <button className="apply-btn" onClick={applyFilters}><Search size={16} /> Применить</button>
            <button className="reset-btn" onClick={resetFilters}><RotateCcw size={16} /> Сбросить</button>
          </div>
        </div>
      </div>

      {offices.length === 0 ? (
        <div className="empty-state">
          <Building2 size={64} strokeWidth={1.5} />
          <h3>Нет офисов</h3>
          <p>Нет офисов, соответствующих критериям поиска</p>
        </div>
      ) : (
        <div className="offices-grid">
          {offices.map(office => <OfficeCard key={office.id} office={office} />)}
        </div>
      )}
    </div>
  );
};

export default DashboardPage;