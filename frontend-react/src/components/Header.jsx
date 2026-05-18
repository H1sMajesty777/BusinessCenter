// frontend/src/components/Header.jsx - обновленная версия

import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Building2, BarChart3, User, Settings, LogOut, LogIn,
  Menu, X, ChevronRight, FileText, Heart
} from 'lucide-react';
import '../styles/header.css';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const isAuthenticated = !!user;
  const roleId = user?.role_id;
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 910);
  
  const isAuthPage = location.pathname === '/auth' || location.pathname === '/login' || location.pathname === '/register';
  
  if (isAuthPage) return null;

  useEffect(() => {
    document.body.style.paddingTop = '70px';
    return () => { document.body.style.paddingTop = '0'; };
  }, []);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 910);
      if (window.innerWidth > 910) setIsMobileMenuOpen(false);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const controlHeader = () => {
      const currentScrollY = window.scrollY;
      if (currentScrollY > lastScrollY && currentScrollY > 50) setIsVisible(false);
      else if (currentScrollY < lastScrollY) setIsVisible(true);
      setLastScrollY(currentScrollY);
    };
    window.addEventListener('scroll', controlHeader);
    return () => window.removeEventListener('scroll', controlHeader);
  }, [lastScrollY]);

  const handleLogout = async () => {
    await logout();
    navigate('/auth');
    setIsMobileMenuOpen(false);
  };

  // Десктопная навигация
  const desktopNav = (
    <nav className="header-nav">
      <Link to="/dashboard" className="header-nav-link">
        <Building2 size={18} style={{ marginRight: '6px' }} />
        Офисы
      </Link>
      
      <Link to="/profile" className="header-nav-link">
        <User size={18} style={{ marginRight: '6px' }} />
        Профиль
      </Link>

      {roleId !== 3 && (
        <Link to="/forecast" className="header-nav-link">
          <BarChart3 size={18} style={{ marginRight: '6px' }} />
          Аналитика
        </Link>
      )}

      {roleId === 2 && (
        <Link to="/manager" className="header-nav-link">
          <FileText size={18} style={{ marginRight: '6px' }} />
          Управление
        </Link>
      )}

      {roleId === 1 && (
        <Link to="/admin" className="header-nav-link">
          <Settings size={18} style={{ marginRight: '6px' }} />
          Админ
        </Link>
      )}
    </nav>
  );

  // Мобильная навигация
  const mobileNav = (
    <div className={`mobile-menu-overlay ${isMobileMenuOpen ? 'open' : ''}`}>
      <div className="mobile-menu-container">
        <div className="mobile-menu-header">
          <span className="mobile-menu-title">Меню</span>
          <button className="mobile-menu-close" onClick={() => setIsMobileMenuOpen(false)}>
            <X size={24} />
          </button>
        </div>
        <nav className="mobile-nav-links">
          <Link to="/dashboard" className="mobile-nav-link" onClick={() => setIsMobileMenuOpen(false)}>
            <Building2 size={20} />
            <span>Офисы</span>
            <ChevronRight size={16} className="mobile-arrow" />
          </Link>
          
          <Link to="/profile" className="mobile-nav-link" onClick={() => setIsMobileMenuOpen(false)}>
            <User size={20} />
            <span>Профиль</span>
            <ChevronRight size={16} className="mobile-arrow" />
          </Link>

          {roleId !== 3 && (
            <Link to="/forecast" className="mobile-nav-link" onClick={() => setIsMobileMenuOpen(false)}>
              <BarChart3 size={20} />
              <span>Аналитика</span>
              <ChevronRight size={16} className="mobile-arrow" />
            </Link>
          )}

          {roleId === 2 && (
            <Link to="/manager" className="mobile-nav-link" onClick={() => setIsMobileMenuOpen(false)}>
              <FileText size={20} />
              <span>Управление</span>
              <ChevronRight size={16} className="mobile-arrow" />
            </Link>
          )}

          {roleId === 1 && (
            <Link to="/admin" className="mobile-nav-link" onClick={() => setIsMobileMenuOpen(false)}>
              <Settings size={20} />
              <span>Админ</span>
              <ChevronRight size={16} className="mobile-arrow" />
            </Link>
          )}

          {isAuthenticated && (
            <button className="mobile-nav-link mobile-logout" onClick={handleLogout}>
              <LogOut size={20} />
              <span>Выйти</span>
              <ChevronRight size={16} className="mobile-arrow" />
            </button>
          )}
        </nav>
        
        {isAuthenticated && (
          <div className="mobile-user-info">
            <div className="mobile-user-name">
              👤 {user?.full_name || user?.login || 'Пользователь'}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      <header className={`header ${isVisible ? 'header-visible' : 'header-hidden'}`}>
        <div className="header-container">
          <Link to="/dashboard" className="header-logo">
            biznes.center
          </Link>

          {!isMobile && isAuthenticated && desktopNav}

          {!isMobile && (
            isAuthenticated ? (
              <div className="header-user">
                <span className="header-user-name">
                  👤 {user?.full_name || user?.login || 'Пользователь'}
                </span>
                <button onClick={handleLogout} className="header-logout-btn">
                  <LogOut size={16} style={{ marginRight: '6px' }} />
                  Выйти
                </button>
              </div>
            ) : (
              <Link to="/auth" className="header-login-btn">
                <LogIn size={16} style={{ marginRight: '6px' }} />
                Войти
              </Link>
            )
          )}

          {isMobile && (
            <div className="mobile-buttons">
              {!isAuthenticated ? (
                <Link to="/auth" className="mobile-login-btn">
                  <LogIn size={20} />
                </Link>
              ) : (
                <button className="mobile-logout-btn" onClick={handleLogout}>
                  <LogOut size={20} />
                </button>
              )}
              <button className="mobile-menu-btn" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
                {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          )}
        </div>
      </header>

      {isMobile && mobileNav}
    </>
  );
};

export default Header;