import api from './api';

// Получить список офисов (с фильтрацией)
export const getOffices = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.floor) params.append('floor', filters.floor);
  if (filters.min_price) params.append('min_price', filters.min_price);
  if (filters.max_price) params.append('max_price', filters.max_price);
  if (filters.is_free !== undefined && filters.is_free !== '') {
    params.append('is_free', filters.is_free);
  }
  const url = params.toString() ? `/offices?${params}` : '/offices';
  const response = await api.get(url);
  return response.data;
};

// Получить один офис по ID
export const getOfficeById = async (id) => {
  const response = await api.get(`/offices/${id}`);
  return response.data;
};

// Создать офис (только для админа)
export const createOffice = async (officeData) => {
  const response = await api.post('/offices', officeData);
  return response.data;
};

// Обновить офис (только для админа)
export const updateOffice = async (id, officeData) => {
  const response = await api.put(`/offices/${id}`, officeData);
  return response.data;
};

// Удалить офис (только для админа)
export const deleteOffice = async (id) => {
  const response = await api.delete(`/offices/${id}`);
  return response.data;
};