// frontend/src/services/api.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,  // ОБЯЗАТЕЛЬНО для отправки HttpOnly Cookie
});

// Переменная для предотвращения множественных refresh запросов
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Перехватчик ответов — автоматический refresh токена
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Если ошибка 401 и это не запрос на refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Если уже идет refresh, ждем
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => {
          return api(originalRequest);
        }).catch((err) => {
          return Promise.reject(err);
        });
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        // Вызываем refresh — кука с refresh_token отправится автоматически
        await api.post('/auth/refresh');
        
        processQueue(null);
        // Повторяем оригинальный запрос — новая access кука уже установлена
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        // Очищаем состояние и редиректим на логин
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    return Promise.reject(error);
  }
);

// ПРИМЕЧАНИЕ: Интерцептор для заголовка Authorization НЕ НУЖЕН!
// Куки отправляются автоматически благодаря withCredentials: true

export default api;