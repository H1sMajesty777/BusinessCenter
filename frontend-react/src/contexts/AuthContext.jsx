// frontend/src/contexts/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Загрузка пользователя из localStorage при запуске
  useEffect(() => {
    // Проверяем, находимся ли мы на странице авторизации
    const isAuthPage = window.location.pathname === '/auth' || 
                       window.location.pathname === '/login' || 
                       window.location.pathname === '/register';
    
    // Если на странице авторизации — не загружаем пользователя
    if (isAuthPage) {
      setLoading(false);
      return;
    }
    
    const storedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    const accessToken = localStorage.getItem('access_token');
    
    if (storedUser && (token || accessToken)) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
        
        // Устанавливаем токен для API запросов
        if (token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        } else if (accessToken) {
          api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
        }
      } catch (e) {
        console.error('Ошибка загрузки пользователя:', e);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        localStorage.removeItem('access_token');
        setUser(null);
      }
    } else {
      // Очищаем всё, если нет данных
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');
      delete api.defaults.headers.common['Authorization'];
      setUser(null);
    }
    
    setLoading(false);
  }, []);

  const login = (userData, token = null) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    
    if (token) {
      localStorage.setItem('token', token);
      localStorage.setItem('access_token', token);
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    delete api.defaults.headers.common['Authorization'];
  };

  const updateUser = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, updateUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
};