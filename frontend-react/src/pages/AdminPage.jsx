import React from 'react';

const AdminPage = () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  if (user.role_id !== 1) {
    return <div style={{ padding: '20px' }}>Доступ запрещён. Только для администраторов.</div>;
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '20px' }}>
      <h1>Админ-панель</h1>
      <p>Добро пожаловать, {user.login}!</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px', marginTop: '20px' }}>
        <div style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
          <h3>👥 Пользователи</h3>
          <p>Управление пользователями системы</p>
          <button>Перейти</button>
        </div>
        <div style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
          <h3>📋 Журнал аудита</h3>
          <p>Просмотр действий пользователей</p>
          <button>Перейти</button>
        </div>
        <div style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
          <h3>💾 Резервное копирование</h3>
          <p>Создание и восстановление бэкапов</p>
          <button>Перейти</button>
        </div>
        <div style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
          <h3>⚙️ Настройки</h3>
          <p>Настройка системы</p>
          <button>Перейти</button>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;