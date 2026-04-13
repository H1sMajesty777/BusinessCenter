import api from './api';

export const login = async (login, password) => {
  const response = await api.post('/auth/login', { login, password });
  return response.data;
};

export const logout = async () => {
  await api.post('/auth/logout');
};

export const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};