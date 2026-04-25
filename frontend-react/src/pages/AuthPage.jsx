// src/pages/AuthPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { Building2, Mail, Lock, User, Phone, Eye, EyeOff } from 'lucide-react';
import '../styles/authPage.css';

const AuthPage = () => {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Форма входа
  const [loginData, setLoginData] = useState({
    login: '',
    password: ''
  });
  
  // Форма регистрации
  const [registerData, setRegisterData] = useState({
    login: '',
    email: '',
    phone: '',
    full_name: '',
    password: '',
    confirm_password: ''
  });

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/auth/login', loginData);
      console.log('Ответ сервера:', response.data);
      
      // Проверяем разные варианты названия поля с токеном
      const token = response.data.token || 
                    response.data.access_token || 
                    response.data.accessToken;
      
      const userData = response.data.user || response.data;
      
      if (token) {
        authLogin(userData, token);
      } else {
        authLogin(userData);
      }
      
      // Редирект по роли
      const roleId = userData.role_id;
      if (roleId === 1) navigate('/admin');
      else if (roleId === 2) navigate('/forecast');
      else navigate('/client-dashboard');
      
    } catch (err) {
      console.error('Ошибка входа:', err.response?.data);
      setError(err.response?.data?.detail || 'Неверный логин или пароль');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    if (registerData.password !== registerData.confirm_password) {
      setError('Пароли не совпадают');
      setLoading(false);
      return;
    }
    
    if (registerData.password.length < 6) {
      setError('Пароль должен содержать минимум 6 символов');
      setLoading(false);
      return;
    }
    
    try {
      await api.post('/users', {
        login: registerData.login,
        password: registerData.password,
        email: registerData.email,
        phone: registerData.phone || null,
        full_name: registerData.full_name || null,
        role_id: 3
      });
      
      // После успешной регистрации переключаемся на форму входа
      setIsLogin(true);
      setRegisterData({
        login: '',
        email: '',
        phone: '',
        full_name: '',
        password: '',
        confirm_password: ''
      });
      setError('');
      // Показываем сообщение об успехе
      alert('Регистрация успешна! Теперь войдите в систему.');
      
    } catch (err) {
      console.error('Ошибка регистрации:', err.response?.data);
      setError(err.response?.data?.detail || 'Ошибка регистрации');
    } finally {
      setLoading(false);
    }
  };

  const toggleForm = () => {
    setIsLogin(!isLogin);
    setError('');
  };

  return (
    <div className="auth-container">
      <div className={`auth-wrapper ${isLogin ? 'show-login' : 'show-register'}`}>
        {/* Левая панель — приветствие */}
        <div className="auth-panel auth-panel-left">
          <div className="panel-content">
            <Building2 size={64} className="panel-icon" />
            <h1 className="panel-title">biznes.center</h1>
            <p className="panel-subtitle">Аренда бизнес-помещений</p>
            <div className="panel-features">
              <div className="feature">✓ 100+ офисов</div>
              <div className="feature">✓ AI анализ спроса</div>
              <div className="feature">✓ Прозрачные условия</div>
            </div>
          </div>
        </div>

        {/* Правая панель — форма */}
        <div className="auth-panel auth-panel-right">
          <div className="form-container">
            {/* Форма входа */}
            <div className="auth-form login-form">
              <h2 className="form-title">Вход в систему</h2>
              <p className="form-subtitle">Добро пожаловать обратно!</p>
              
              {error && <div className="error-message">{error}</div>}
              
              <form onSubmit={handleLoginSubmit}>
                <div className="form-group">
                  <User size={18} className="input-icon" />
                  <input
                    type="text"
                    placeholder="Логин"
                    value={loginData.login}
                    onChange={(e) => setLoginData({ ...loginData, login: e.target.value })}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <Lock size={18} className="input-icon" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Пароль"
                    value={loginData.password}
                    onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                    required
                  />
                  <button 
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                
                <button type="submit" className="submit-btn" disabled={loading}>
                  {loading ? 'Вход...' : 'Войти'}
                </button>
              </form>
              
              <div className="form-footer">
                Нет аккаунта?{' '}
                <button type="button" onClick={toggleForm} className="toggle-btn">
                  Зарегистрироваться
                </button>
              </div>
            </div>

            {/* Форма регистрации */}
            <div className="auth-form register-form">
              <h2 className="form-title">Регистрация</h2>
              <p className="form-subtitle">Создайте свой аккаунт</p>
              
              {error && <div className="error-message">{error}</div>}
              
              <form onSubmit={handleRegisterSubmit}>
                <div className="form-group">
                  <User size={18} className="input-icon" />
                  <input
                    type="text"
                    placeholder="Логин *"
                    value={registerData.login}
                    onChange={(e) => setRegisterData({ ...registerData, login: e.target.value })}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <Mail size={18} className="input-icon" />
                  <input
                    type="email"
                    placeholder="Email *"
                    value={registerData.email}
                    onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <Phone size={18} className="input-icon" />
                  <input
                    type="tel"
                    placeholder="Телефон"
                    value={registerData.phone}
                    onChange={(e) => setRegisterData({ ...registerData, phone: e.target.value })}
                  />
                </div>
                
                <div className="form-group">
                  <User size={18} className="input-icon" />
                  <input
                    type="text"
                    placeholder="ФИО"
                    value={registerData.full_name}
                    onChange={(e) => setRegisterData({ ...registerData, full_name: e.target.value })}
                  />
                </div>
                
                <div className="form-group">
                  <Lock size={18} className="input-icon" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Пароль *"
                    value={registerData.password}
                    onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <Lock size={18} className="input-icon" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Подтвердите пароль *"
                    value={registerData.confirm_password}
                    onChange={(e) => setRegisterData({ ...registerData, confirm_password: e.target.value })}
                    required
                  />
                  <button 
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                
                <button type="submit" className="submit-btn" disabled={loading}>
                  {loading ? 'Регистрация...' : 'Зарегистрироваться'}
                </button>
              </form>
              
              <div className="form-footer">
                Уже есть аккаунт?{' '}
                <button type="button" onClick={toggleForm} className="toggle-btn">
                  Войти
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;