// frontend/src/components/Header.jsx
import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Building2, BarChart3, User, Settings, LogOut, LogIn, Heart,
  Menu, X, ChevronRight, FileText 
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
  
  // Скрываем хедер на странице авторизации
  const isAuthPage = location.pathname === '/auth' || location.pathname === '/login' || location.pathname === '/register';
  
  if (isAuthPage) {
    return null; // Ничего не рендерим на странице авторизации
  }

  // Управление отступом body
  useEffect(() => {
    document.body.style.paddingTop = '70px';
    return () => {
      document.body.style.paddingTop = '0';
    };
  }, []);

  // Проверка ширины экрана
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 910);
      if (window.innerWidth > 910) {
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Скрытие хедера при скролле
  useEffect(() => {
    const controlHeader = () => {
      const currentScrollY = window.scrollY;
      if (currentScrollY > lastScrollY && currentScrollY > 50) {
        setIsVisible(false);
      } else if (currentScrollY < lastScrollY) {
        setIsVisible(true);
      }
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

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  // Десктопная навигация
  const desktopNav = (
    <nav className="header-nav">
      <Link to="/dashboard" className="header-nav-link" onClick={closeMobileMenu}>
        <Building2 size={18} style={{ marginRight: '6px' }} />
        Офисы
      </Link>

      {roleId !== 3 && (
        <Link to="/forecast" className="header-nav-link" onClick={closeMobileMenu}>
          <BarChart3 size={18} style={{ marginRight: '6px' }} />
          Аналитика
        </Link>
      )}

      {roleId === 3 && (
        <>
          <Link to="/client-dashboard" className="header-nav-link" onClick={closeMobileMenu}>
            <User size={18} style={{ marginRight: '6px' }} />
            Личный кабинет
          </Link>
        </>
      )}

      {roleId === 1 && (
        <Link to="/admin" className="header-nav-link" onClick={closeMobileMenu}>
          <Settings size={18} style={{ marginRight: '6px' }} />
          Админ
        </Link>
      )}

      {roleId === 2 && (
        <Link to="/manager" className="header-nav-link">
          <FileText size={18} style={{ marginRight: '6px' }} />
          Управление
        </Link>
      )}
    </nav>
  );

  // Мобильная навигация (бургер-меню)
  const mobileNav = (
    <div className={`mobile-menu-overlay ${isMobileMenuOpen ? 'open' : ''}`}>
      <div className="mobile-menu-container">
        <div className="mobile-menu-header">
          <span className="mobile-menu-title">Меню</span>
          <button className="mobile-menu-close" onClick={toggleMobileMenu}>
            <X size={24} />
          </button>
        </div>
        <nav className="mobile-nav-links">
          <Link to="/dashboard" className="mobile-nav-link" onClick={closeMobileMenu}>
            <Building2 size={20} />
            <span>Офисы</span>
            <ChevronRight size={16} className="mobile-arrow" />
          </Link>

          {roleId !== 3 && (
            <Link to="/forecast" className="mobile-nav-link" onClick={closeMobileMenu}>
              <BarChart3 size={20} />
              <span>Аналитика</span>
              <ChevronRight size={16} className="mobile-arrow" />
            </Link>
          )}

          {roleId === 3 && (
            <>
              <Link to="/client-dashboard" className="mobile-nav-link" onClick={closeMobileMenu}>
                <User size={20} />
                <span>Личный кабинет</span>
                <ChevronRight size={16} className="mobile-arrow" />
              </Link>
            </>
          )}

          {roleId === 1 && (
            <Link to="/admin" className="mobile-nav-link" onClick={closeMobileMenu}>
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
              👤 {user?.login || 'Пользователь'}
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
          <Link to="/dashboard" className="header-logo" onClick={closeMobileMenu}>
            biznes.center
          </Link>

          {/* Десктопная навигация */}
          {!isMobile && isAuthenticated && desktopNav}

          {/* Правая часть */}
          {!isMobile && (
            isAuthenticated ? (
              <div className="header-user">
                <span className="header-user-name">
                  👤 {user?.login || 'Пользователь'}
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

          {/* Мобильная кнопка меню */}
          {isMobile && (
            <div className="mobile-buttons">
              {!isAuthenticated ? (
                <Link to="/auth" className="mobile-login-btn" onClick={closeMobileMenu}>
                  <LogIn size={20} />
                </Link>
              ) : (
                <button className="mobile-logout-btn" onClick={handleLogout}>
                  <LogOut size={20} />
                </button>
              )}
              <button className="mobile-menu-btn" onClick={toggleMobileMenu}>
                {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Мобильное меню */}
      {isMobile && mobileNav}
    </>
  );
};

export default Header;