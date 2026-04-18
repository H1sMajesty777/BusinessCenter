import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import '../styles/register.css';

const RegisterPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    login: '',
    email: '',
    phone: '',
    full_name: '',
    password: '',
    confirm_password: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    
    if (!formData.login.trim()) {
      newErrors.login = 'Логин обязателен';
    } else if (formData.login.length < 3) {
      newErrors.login = 'Логин должен содержать минимум 3 символа';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email обязателен';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Введите корректный email';
    }
    
    if (!formData.password) {
      newErrors.password = 'Пароль обязателен';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Пароль должен содержать минимум 6 символов';
    }
    
    if (formData.password !== formData.confirm_password) {
      newErrors.confirm_password = 'Пароли не совпадают';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    
    setLoading(true);
    setServerError('');
    
    try {
      await api.post('/users', {
        login: formData.login,
        password: formData.password,
        email: formData.email,
        phone: formData.phone || null,
        full_name: formData.full_name || null,
        role_id: 3
      });
      
      navigate('/login', { state: { message: 'Регистрация успешна! Теперь войдите в систему.' } });
    } catch (error) {
      if (error.response?.data?.detail) {
        setServerError(error.response.data.detail);
      } else {
        setServerError('Ошибка регистрации. Попробуйте позже.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <h2 className="register-title">Регистрация</h2>
        <p className="register-subtitle">Создайте аккаунт, чтобы арендовать офис</p>
        
        {serverError && <div className="register-error-banner">{serverError}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="register-field">
            <label className="register-label">Логин *</label>
            <input
              type="text"
              name="login"
              value={formData.login}
              onChange={handleChange}
              className={`register-input ${errors.login ? 'error' : ''}`}
            />
            {errors.login && <p className="register-field-error">{errors.login}</p>}
          </div>
          
          <div className="register-field">
            <label className="register-label">Email *</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={`register-input ${errors.email ? 'error' : ''}`}
            />
            {errors.email && <p className="register-field-error">{errors.email}</p>}
          </div>
          
          <div className="register-field">
            <label className="register-label">Телефон</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="register-input"
              placeholder="+7 (999) 123-45-67"
            />
          </div>
          
          <div className="register-field">
            <label className="register-label">ФИО</label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              className="register-input"
              placeholder="Иванов Иван Иванович"
            />
          </div>
          
          <div className="register-field">
            <label className="register-label">Пароль *</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={`register-input ${errors.password ? 'error' : ''}`}
            />
            {errors.password && <p className="register-field-error">{errors.password}</p>}
          </div>
          
          <div className="register-field">
            <label className="register-label">Подтверждение пароля *</label>
            <input
              type="password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              className={`register-input ${errors.confirm_password ? 'error' : ''}`}
            />
            {errors.confirm_password && <p className="register-field-error">{errors.confirm_password}</p>}
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="register-btn"
          >
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>
        
        <div className="register-footer">
          Уже есть аккаунт? <Link to="/login" className="register-link">Войти</Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;