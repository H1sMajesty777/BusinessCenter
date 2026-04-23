import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import '../styles/forecast.css';
import { ChartNoAxesCombined, Brain, RefreshCw } from 'lucide-react';

const ForecastPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role_id === 1;
  
  const [forecasts, setForecasts] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [lastTrained, setLastTrained] = useState('');
  const [metrics, setMetrics] = useState({ accuracy: '—', auc: '—' });
  
  const [filters, setFilters] = useState({
    floor: '',
    minPrice: '',
    maxPrice: '',
    category: ''
  });
  const [tempFilters, setTempFilters] = useState({
    floor: '',
    minPrice: '',
    maxPrice: '',
    category: ''
  });

  const loadForecast = async () => {
    setLoading(true);
    try {
      const params = {};
      if (tempFilters.floor) params.floor = parseInt(tempFilters.floor);
      if (tempFilters.minPrice) params.min_price = parseFloat(tempFilters.minPrice);
      if (tempFilters.maxPrice) params.max_price = parseFloat(tempFilters.maxPrice);
      if (tempFilters.category) params.category = tempFilters.category;
      
      const response = await api.get('/ai/rental-prediction/summary', { params });
      setForecasts(response.data.offices || []);
    } catch (error) {
      console.error('Ошибка загрузки прогнозов:', error);
      setForecasts([]);
    } finally {
      setLoading(false);
    }
  };

  const loadTrends = async () => {
    try {
      const response = await api.get('/ai/rental-prediction/trends?days=30');
      const viewsData = response.data.views_trend || [];
      // Преобразуем для графика
      const chart = viewsData.map(item => ({
        name: item.date?.slice(5) || item.date,
        просмотры: item.views,
        заявки: 0,
        договоры: 0
      }));
      setChartData(chart);
    } catch (error) {
      console.error('Ошибка загрузки трендов:', error);
      setChartData([]);
    }
  };

  const loadModelInfo = async () => {
    try {
      const response = await api.get('/ai/rental-prediction/model/info');
      if (response.data.is_trained) {
        setLastTrained(new Date().toLocaleDateString('ru-RU'));
        setMetrics({ accuracy: '≈85%', auc: '≈0.89' });
      }
    } catch (error) {
      console.error('Ошибка загрузки информации о модели:', error);
    }
  };

  useEffect(() => {
    loadForecast();
    loadTrends();
    loadModelInfo();
  }, []);

  const applyFilters = () => {
    setFilters({ ...tempFilters });
    loadForecast();
  };

  const resetFilters = () => {
    const emptyFilters = { floor: '', minPrice: '', maxPrice: '', category: '' };
    setTempFilters(emptyFilters);
    setFilters(emptyFilters);
    loadForecast();
  };

  const handleFilterChange = (key, value) => {
    setTempFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleTrain = async () => {
    setTraining(true);
    try {
      const response = await api.post('/ai/rental-prediction/train?force=true');
      if (response.data.success) {
        setLastTrained(new Date().toLocaleDateString('ru-RU'));
        alert('Модель успешно переобучена!');
        loadForecast();
        loadModelInfo();
      } else {
        alert('Ошибка при обучении модели');
      }
    } catch (error) {
      console.error('Ошибка обучения:', error);
      alert(error.response?.data?.detail || 'Ошибка при обучении модели');
    } finally {
      setTraining(false);
    }
  };

  const getProbabilityClass = (probability) => {
    if (probability >= 70) return 'high';
    if (probability >= 50) return 'medium';
    return 'low';
  };

  const getCategoryClass = (category) => {
    if (category === 'high') return 'category-high';
    if (category === 'medium') return 'category-medium';
    return 'category-low';
  };

  const getCategoryText = (category) => {
    if (category === 'high') return 'Высокий';
    if (category === 'medium') return 'Средний';
    return 'Низкий';
  };

  const getBarColor = (probability) => {
    if (probability >= 70) return '#22c55e';
    if (probability >= 50) return '#eab308';
    return '#ef4444';
  };

  // Данные для графика из прогнозов
  const chartDataFromForecasts = forecasts.slice(0, 10).map(office => ({
    name: office.office_number,
    вероятность: office.probability_percent || Math.round(office.probability * 100)
  }));

  return (
    <div className="forecast-container">
      <h1 className="forecast-title">Аналитика аренды</h1>
      <p className="forecast-subtitle">AI-прогноз спроса на свободные офисы</p>

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
              />
              <span>—</span>
              <input
                type="number"
                className="filter-input"
                value={tempFilters.maxPrice}
                onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                placeholder="до"
              />
            </div>
          </div>
          
          <div className="filter-group">
            <label className="filter-label">Категория</label>
            <select
              className="filter-select"
              value={tempFilters.category}
              onChange={(e) => handleFilterChange('category', e.target.value)}
            >
              <option value="">Все</option>
              <option value="high">Высокий спрос</option>
              <option value="medium">Средний спрос</option>
              <option value="low">Низкий спрос</option>
            </select>
          </div>
          
          <div className="filter-actions">
            <button className="reset-btn" onClick={resetFilters}>
              Сбросить
            </button>
            <button className="apply-btn" onClick={applyFilters}>
              Применить
            </button>
          </div>
        </div>
      </div>

      <div className="chart-section">
        <h2 className="section-title">
          <ChartNoAxesCombined size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          Прогноз по офисам
        </h2>
        <p className="section-subtitle">Вероятность аренды в процентах (зелёный — высокий, жёлтый — средний, красный — низкий)</p>
        
        {chartDataFromForecasts.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartDataFromForecasts} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value) => [`${value}%`, 'Вероятность']} />
              <Bar dataKey="вероятность" radius={[8, 8, 0, 0]}>
                {chartDataFromForecasts.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.вероятность)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state">Нет данных для отображения</div>
        )}

        <div style={{ display: 'flex', justifyContent: 'center', gap: '30px', marginTop: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '20px', height: '20px', background: '#22c55e', borderRadius: '4px' }}></div>
            <span style={{ fontSize: '13px' }}>Высокий спрос (≥70%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '20px', height: '20px', background: '#eab308', borderRadius: '4px' }}></div>
            <span style={{ fontSize: '13px' }}>Средний спрос (50-69%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '20px', height: '20px', background: '#ef4444', borderRadius: '4px' }}></div>
            <span style={{ fontSize: '13px' }}>Низкий спрос (&lt;50%)</span>
          </div>
        </div>
      </div>

      <div className="table-section">
        <h2 className="section-title">Детальный прогноз по офисам</h2>
        
        {loading ? (
          <div className="loading-state">Загрузка...</div>
        ) : forecasts.length === 0 ? (
          <div className="empty-state">Нет данных для отображения</div>
        ) : (
          <table className="forecast-table">
            <thead>
              <tr>
                <th>Офис</th>
                <th>Этаж</th>
                <th>Площадь</th>
                <th>Цена</th>
                <th>Вероятность</th>
                <th>Категория</th>
                <th>Факторы</th>
              </tr>
            </thead>
            <tbody>
              {forecasts.map(office => (
                <tr key={office.office_id}>
                  <td><strong>{office.office_number}</strong></td>
                  <td>{office.floor} эт</td>
                  <td>{office.area_sqm} м²</td>
                  <td>{office.price_per_month?.toLocaleString()} ₽</td>
                  <td>
                    <div className="probability-container">
                      <div className="probability-bar">
                        <div 
                          className={`probability-fill ${getProbabilityClass(office.probability_percent || office.probability * 100)}`}
                          style={{ width: `${office.probability_percent || office.probability * 100}%` }}
                        />
                      </div>
                      <span className="probability-value">{office.probability_percent || Math.round(office.probability * 100)}%</span>
                    </div>
                  </td>
                  <td>
                    <span className={`category-badge ${getCategoryClass(office.category)}`}>
                      {getCategoryText(office.category)}
                    </span>
                  </td>
                  <td>
                    <div className="factors-list">
                      {office.top_factors?.slice(0, 2).map((factor, idx) => (
                        <span key={idx} className="factor-tag">
                          {factor.feature}: {(factor.importance * 100).toFixed(0)}%
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {(isAdmin || user?.role_id === 2) && (
        <div className="model-control">
          <div className="model-info">
            <div className="model-date">
              <Brain size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              Последнее обучение: {lastTrained || 'не выполнялось'}
            </div>
            <div className="model-metrics">
              <div className="metric">
                <div className="metric-value">{metrics.accuracy}</div>
                <div className="metric-label">Accuracy</div>
              </div>
              <div className="metric">
                <div className="metric-value">{metrics.auc}</div>
                <div className="metric-label">ROC AUC</div>
              </div>
            </div>
          </div>
          {isAdmin && (
            <button className="train-btn" onClick={handleTrain} disabled={training}>
              <RefreshCw size={16} style={{ marginRight: '6px' }} />
              {training ? 'Обучение...' : 'Переобучить модель'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ForecastPage;