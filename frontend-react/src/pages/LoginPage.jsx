// frontend/src/pages/LoginPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import '../styles/login.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login: authLogin } = useAuth();
  const [loginValue, setLoginValue] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      // Шаг 1: Логин — бэкенд устанавливает HttpOnly Cookie
      await api.post('/auth/login', { login: loginValue, password });
      
      // Токены теперь в куках, localStorage не трогаем!
      
      // Шаг 2: Получаем пользователя (кука отправляется автоматически)
      const userResponse = await api.get('/auth/me');
      authLogin(userResponse.data);
      
      // Шаг 3: Редирект по роли
      const roleId = userResponse.data.role_id;
      if (roleId === 1) navigate('/admin');
      else if (roleId === 2) navigate('/forecast');
      else navigate('/client-dashboard');
    } catch (err) {
      setError('Неверный логин или пароль');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2 className="login-title">Вход в систему</h2>
        <p className="login-subtitle">Бизнес-центр · аренда офисов</p>
        
        {successMessage && <div className="login-success-banner">{successMessage}</div>}
        {error && <div className="login-error-banner">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="login-field">
            <label className="login-label">Логин</label>
            <input
              type="text"
              value={loginValue}
              onChange={(e) => setLoginValue(e.target.value)}
              className="login-input"
              required
            />
          </div>
          
          <div className="login-field">
            <label className="login-label">Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="login-input"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="login-btn"
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
        
        <div className="login-footer">
          Нет аккаунта? <Link to="/register" className="login-link">Зарегистрироваться</Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;