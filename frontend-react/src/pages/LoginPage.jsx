import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Мок-проверка
    if (login === 'admin' && password === 'admin123') {
      localStorage.setItem('user', JSON.stringify({ login, role_id: 1 }));
      navigate('/dashboard');
    } else if (login === 'manager' && password === 'manager123') {
      localStorage.setItem('user', JSON.stringify({ login, role_id: 2 }));
      navigate('/dashboard');
    } else if (login === 'client' && password === 'client123') {
      localStorage.setItem('user', JSON.stringify({ login, role_id: 3 }));
      navigate('/dashboard');
    } else {
      setError('Неверный логин или пароль');
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px' }}>
      <h2>Вход в систему</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label>Логин</label>
          <input
            type="text"
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            style={{ width: '100%', padding: '8px', margin: '8px 0' }}
            required
          />
        </div>
        <div>
          <label>Пароль</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: '8px', margin: '8px 0' }}
            required
          />
        </div>
        <button type="submit" style={{ padding: '10px 20px', marginTop: '10px' }}>
          Войти
        </button>
      </form>
    </div>
  );
};

export default LoginPage;