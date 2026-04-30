// frontend/src/contexts/AuthContext.jsx

import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Проверка авторизации при загрузке приложения
  useEffect(() => {
    const checkAuth = async () => {
      // Не проверяем на странице авторизации
      const isAuthPage = window.location.pathname === '/auth' || 
                         window.location.pathname === '/login' || 
                         window.location.pathname === '/register';
      
      if (isAuthPage) {
        setLoading(false);
        return;
      }
      
      try {
        // Пытаемся получить текущего пользователя
        // Кука access_token отправится автоматически (withCredentials: true)
        const response = await api.get('/auth/me');
        
        if (response.data) {
          setUser(response.data);
          console.log('✅ Авторизация восстановлена:', response.data.login);
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('❌ Ошибка проверки авторизации:', error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const login = async (loginData, token = null) => {
    // При логине сохраняем пользователя в state
    setUser(loginData);
    // Не сохраняем токен в localStorage — он уже в Cookie!
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Ошибка при выходе:', error);
    } finally {
      setUser(null);
      // Не чистим localStorage — там ничего нет!
    }
  };

  const updateUser = (userData) => {
    setUser(userData);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, updateUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
};