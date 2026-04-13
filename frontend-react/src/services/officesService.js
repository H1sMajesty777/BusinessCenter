import api from './api';

export const getOffices = async (filters = {}) => {
  const params = new URLSearchParams(filters).toString();
  const url = params ? `/offices?${params}` : '/offices';
  const response = await api.get(url);
  return response.data;
};

export const getOfficeById = async (id) => {
  const response = await api.get(`/offices/${id}`);
  return response.data;
};