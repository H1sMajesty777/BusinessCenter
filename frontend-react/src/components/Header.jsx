import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Header = () => {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const isAuthenticated = !!localStorage.getItem('user');

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <header style={{
      background: '#1e293b',
      color: 'white',
      padding: '15px 20px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '15px'
      }}>
        {/* Логотип */}
        <Link to="/dashboard" style={{
          fontSize: '24px',
          fontWeight: 'bold',
          color: '#ffd5a1',
          textDecoration: 'none'
        }}>
          biznes.center
        </Link>

        {/* Навигация (видна только авторизованным) */}
        {isAuthenticated && (
          <nav style={{
            display: 'flex',
            gap: '25px',
            alignItems: 'center',
            flexWrap: 'wrap'
          }}>
            <Link to="/dashboard" style={{
              color: 'white',
              textDecoration: 'none',
              padding: '5px 10px',
              borderRadius: '8px',
              transition: 'background 0.2s'
            }} onMouseEnter={(e) => e.target.style.background = '#334155'}
               onMouseLeave={(e) => e.target.style.background = 'transparent'}>
              🏢 Офисы
            </Link>

            <Link to="/forecast" style={{
              color: 'white',
              textDecoration: 'none',
              padding: '5px 10px',
              borderRadius: '8px',
              transition: 'background 0.2s'
            }} onMouseEnter={(e) => e.target.style.background = '#334155'}
               onMouseLeave={(e) => e.target.style.background = 'transparent'}>
              📊 Прогноз
            </Link>

            <Link to="/contracts" style={{
              color: 'white',
              textDecoration: 'none',
              padding: '5px 10px',
              borderRadius: '8px',
              transition: 'background 0.2s'
            }} onMouseEnter={(e) => e.target.style.background = '#334155'}
               onMouseLeave={(e) => e.target.style.background = 'transparent'}>
              📄 Договоры
            </Link>

            {/* Админка (только для role_id === 1) */}
            {user.role_id === 1 && (
              <Link to="/admin" style={{
                color: '#ffd5a1',
                textDecoration: 'none',
                padding: '5px 10px',
                borderRadius: '8px',
                transition: 'background 0.2s'
              }} onMouseEnter={(e) => e.target.style.background = '#334155'}
                 onMouseLeave={(e) => e.target.style.background = 'transparent'}>
                ⚙️ Админ
              </Link>
            )}
          </nav>
        )}

        {/* Правая часть: имя пользователя и выход */}
        {isAuthenticated ? (
          <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
            <span style={{ color: '#ffd5a1' }}>
              👤 {user.login || 'Пользователь'}
            </span>
            <button onClick={handleLogout} style={{
              background: '#dc2626',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'background 0.2s'
            }} onMouseEnter={(e) => e.target.style.background = '#b91c1c'}
               onMouseLeave={(e) => e.target.style.background = '#dc2626'}>
              Выйти
            </button>
          </div>
        ) : (
          <Link to="/login" style={{
            color: '#ffd5a1',
            textDecoration: 'none',
            padding: '8px 20px',
            border: '1px solid #ffd5a1',
            borderRadius: '8px',
            transition: 'all 0.2s'
          }} onMouseEnter={(e) => {
            e.target.style.background = '#ffd5a1';
            e.target.style.color = '#1e293b';
          }} onMouseLeave={(e) => {
            e.target.style.background = 'transparent';
            e.target.style.color = '#ffd5a1';
          }}>
            Войти
          </Link>
        )}
      </div>
    </header>
  );
};

export default Header;