// frontend/src/pages/ForecastPage.jsx (упрощённый с хуком)
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import useAnalytics from '../hooks/useAnalytics';
import { Brain, RefreshCw, Filter, Download } from 'lucide-react';
import KPICards from '../components/analytics/KPICards';
import TrendsChart from '../components/analytics/TrendsChart';
import OfficesTable from '../components/analytics/OfficesTable';
import OfficeDetailModal from '../components/analytics/OfficeDetailModal';
import '../styles/forecast.css';

const ForecastPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role_id === 1;
  const isManagerOrAdmin = user?.role_id === 1 || user?.role_id === 2;
  
  const {
    loading,
    offices,
    stats,
    trends,
    modelInfo,
    error,
    filters,
    updateFilters,
    trainModel,
    exportToCSV,
    refresh
  } = useAnalytics();
  
  const [selectedOffice, setSelectedOffice] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [training, setTraining] = useState(false);
  
  const handleTrain = async () => {
    setTraining(true);
    const result = await trainModel();
    if (result.success) {
      alert('✅ Модель успешно переобучена!');
    } else {
      alert(`❌ Ошибка: ${result.error}`);
    }
    setTraining(false);
  };
  
  if (!isManagerOrAdmin) {
    return (
      <div className="forecast-access-denied">
        <Building2 size={64} />
        <h2>Доступ ограничен</h2>
        <p>Только менеджеры и администраторы могут просматривать аналитику</p>
      </div>
    );
  }
  
  const lastTrained = modelInfo?.metadata?.trained_at ? new Date(modelInfo.metadata.trained_at) : null;
  
  return (
    <div className="forecast-page">
      {/* Hero секция */}
      <div className="forecast-hero">
        <div className="hero-content">
          <div>
            <h1 className="hero-title">
              <Brain className="hero-icon" size={32} />
              AI-аналитика аренды
            </h1>
            <p className="hero-subtitle">
              Интеллектуальный анализ спроса и прогнозирование аренды офисов
            </p>
          </div>
          <div className="hero-actions">
            <button className="btn-outline" onClick={() => setShowFilters(!showFilters)}>
              <Filter size={16} />
              Фильтры
            </button>
            <button className="btn-outline" onClick={exportToCSV}>
              <Download size={16} />
              Экспорт
            </button>
            {isAdmin && (
              <button className="btn-primary" onClick={handleTrain} disabled={training}>
                <RefreshCw size={16} className={training ? 'spinning' : ''} />
                {training ? 'Обучение...' : 'Переобучить модель'}
              </button>
            )}
          </div>
        </div>
        
        {/* Панель фильтров */}
        {showFilters && (
          <div className="filters-panel">
            <div className="filters-grid">
              <div className="filter-group">
                <label>Категория спроса</label>
                <select 
                  value={filters.category} 
                  onChange={(e) => updateFilters({ category: e.target.value })}
                >
                  <option value="all">Все офисы</option>
                  <option value="high">Высокий спрос (≥70%)</option>
                  <option value="medium">Средний спрос (40-69%)</option>
                  <option value="low">Низкий спрос (&lt;40%)</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label>Сортировка</label>
                <select 
                  value={filters.sortBy} 
                  onChange={(e) => updateFilters({ sortBy: e.target.value })}
                >
                  <option value="probability">По вероятности (убывание)</option>
                  <option value="price">По цене (убывание)</option>
                  <option value="floor">По этажу (возрастание)</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label>Поиск по офису</label>
                <input 
                  type="text" 
                  placeholder="Номер офиса..."
                  value={filters.search}
                  onChange={(e) => updateFilters({ search: e.target.value })}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* KPI Карточки */}
      {stats && <KPICards stats={stats} offices={offices} />}

      {/* График трендов */}
      {trends && <TrendsChart data={trends} />}

      {/* Таблица офисов */}
      <OfficesTable 
        offices={offices} 
        loading={loading}
        error={error}
        onSelectOffice={(office) => {
          setSelectedOffice(office);
          setShowDetailModal(true);
        }}
      />

      {/* Модальное окно */}
      {showDetailModal && selectedOffice && (
        <OfficeDetailModal 
          office={selectedOffice}
          onClose={() => setShowDetailModal(false)}
        />
      )}

      {/* Статус модели */}
      {lastTrained && (
        <div className="model-status">
          <div className="status-content">
            <Brain size={16} />
            <span>Модель обучена: {lastTrained.toLocaleDateString('ru-RU', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}</span>
            <div className="status-dot" />
            <span>Актуальность: {Math.floor((new Date() - lastTrained) / (1000 * 60 * 60 * 24))} дней</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ForecastPage;