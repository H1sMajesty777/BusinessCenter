// frontend/src/services/favoritesService.js

import api from './api';

// Получить все избранные офисы
export const getFavorites = async () => {
  const response = await api.get('/favorites');
  return response.data;
};

// Добавить в избранное
export const addFavorite = async (officeId) => {
  const response = await api.post('/favorites', { office_id: officeId });
  return response.data;
};

// Удалить из избранного
export const removeFavorite = async (officeId) => {
  const response = await api.delete(`/favorites/${officeId}`);
  return response.data;
};

// Проверить, в избранном ли офис
export const checkFavorite = async (officeId) => {
  const response = await api.get(`/favorites/check/${officeId}`);
  return response.data.is_favorite;
};