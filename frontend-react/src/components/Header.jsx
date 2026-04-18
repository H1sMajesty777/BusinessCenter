import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/header.css';

const Header = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const isAuthenticated = !!user;
  const roleId = user?.role_id;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="header">
      <div className="header-container">
        {/* Логотип */}
        <Link to="/dashboard" className="header-logo">
          biznes.center
        </Link>

        {/* Навигация (только для авторизованных) */}
        {isAuthenticated && (
          <nav className="header-nav">
            {/* Офисы — видят все */}
            <Link to="/dashboard" className="header-nav-link">
              🏢 Офисы
            </Link>

            {/* Аналитика — только менеджер (role_id=2) и админ (role_id=1) */}
            {roleId !== 3 && (
              <Link to="/forecast" className="header-nav-link">
                📊 Аналитика
              </Link>
            )}

            {/* Личный кабинет — только клиент (role_id=3) */}
            {roleId === 3 && (
              <Link to="/client-dashboard" className="header-nav-link">
                👤 Личный кабинет
              </Link>
            )}

            {/* Админка — только админ (role_id=1) */}
            {roleId === 1 && (
              <Link to="/admin" className="header-nav-link">
                ⚙️ Админ
              </Link>
            )}
          </nav>
        )}

        {/* Правая часть */}
        {isAuthenticated ? (
          <div className="header-user">
            <span className="header-user-name">
              👤 {user?.login || 'Пользователь'}
            </span>
            <button onClick={handleLogout} className="header-logout-btn">
              Выйти
            </button>
          </div>
        ) : (
          <Link to="/login" className="header-login-btn">
            Войти
          </Link>
        )}
      </div>
    </header>
  );
};

export default Header;