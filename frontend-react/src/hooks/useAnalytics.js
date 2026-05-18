// frontend/src/hooks/useAnalytics.js
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export const useAnalytics = () => {
  const [loading, setLoading] = useState(true);
  const [offices, setOffices] = useState([]);
  const [stats, setStats] = useState(null);
  const [trends, setTrends] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [error, setError] = useState(null);
  
  const [filters, setFilters] = useState({
    category: 'all',
    sortBy: 'probability',
    search: ''
  });

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Загружаем прогнозы
      const forecastResponse = await api.get('/ai/rental-prediction/summary');
      const officesData = forecastResponse.data.offices || [];
      
      // Загружаем статистику
      setStats(forecastResponse.data.statistics);
      
      // Загружаем тренды
      const trendsResponse = await api.get('/ai/rental-prediction/trends?days=30');
      setTrends(trendsResponse.data);
      
      // Загружаем информацию о модели
      const modelResponse = await api.get('/ai/rental-prediction/model/info');
      setModelInfo(modelResponse.data);
      
      // Применяем фильтры
      let filtered = [...officesData];
      
      if (filters.category !== 'all') {
        filtered = filtered.filter(o => o.category === filters.category);
      }
      
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filtered = filtered.filter(o => 
          o.office_number?.toLowerCase().includes(searchLower) ||
          o.office_id?.toString().includes(searchLower)
        );
      }
      
      // Сортировка
      filtered.sort((a, b) => {
        switch (filters.sortBy) {
          case 'probability':
            return (b.probability || 0) - (a.probability || 0);
          case 'price':
            return (b.price_per_month || 0) - (a.price_per_month || 0);
          case 'floor':
            return (a.floor || 0) - (b.floor || 0);
          default:
            return 0;
        }
      });
      
      setOffices(filtered);
      
    } catch (err) {
      console.error('Ошибка загрузки аналитики:', err);
      setError(err.response?.data?.detail || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const updateFilters = (newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const trainModel = async () => {
    try {
      const response = await api.post('/ai/rental-prediction/train?force=true');
      if (response.data.success) {
        await loadAnalytics();
        return { success: true };
      }
      return { success: false, error: 'Ошибка обучения' };
    } catch (err) {
      console.error('Ошибка обучения:', err);
      return { success: false, error: err.response?.data?.detail || 'Ошибка обучения' };
    }
  };

  const exportToCSV = () => {
    const headers = ['Офис', 'Этаж', 'Площадь', 'Цена', 'Вероятность', 'Категория'];
    const rows = offices.map(o => [
      o.office_number,
      o.floor,
      o.area_sqm,
      o.price_per_month,
      `${Math.round((o.probability || 0) * 100)}%`,
      o.category === 'high' ? 'Высокий' : o.category === 'medium' ? 'Средний' : 'Низкий'
    ]);
    
    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.setAttribute('download', `analytics_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return {
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
    refresh: loadAnalytics
  };
};

export default useAnalytics;