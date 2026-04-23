// frontend/src/contexts/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Загрузка пользователя при старте
  useEffect(() => {
    const loadUser = async () => {
      try {
        // Пробуем загрузить пользователя через куку
        const response = await api.get('/auth/me');
        setUser(response.data);
      } catch (error) {
        // Если нет куки или она истекла — пользователь не авторизован
        console.log('Пользователь не авторизован');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    
    loadUser();
  }, []);

  const login = (userData) => {
    setUser(userData);
    // Сохраняем в localStorage только для удобства (не для безопасности!)
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Ошибка при выходе:', error);
    }
    setUser(null);
    localStorage.removeItem('user');
    // Куки будут удалены бэкендом
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