// frontend/src/pages/ProfilePage.jsx

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { User, Mail, Phone, Lock, Save, UserCircle, FileText, FileCheck, CreditCard } from 'lucide-react';
import '../styles/profile.css';

const ProfilePage = () => {
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    email: ''
  });
  const [passwordData, setPasswordData] = useState({
    new_password: '',
    confirm_password: ''
  });
  const [message, setMessage] = useState({ type: '', text: '' });
  
  // Данные для разных ролей
  const [applications, setApplications] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [payments, setPayments] = useState([]);

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        phone: user.phone || '',
        email: user.email || ''
      });
    }
    
    // Загружаем данные для клиента
    if (user?.role_id === 3) {
      loadMyData();
    }
  }, [user]);

  const loadMyData = async () => {
    try {
      const [apps, contrs, pays] = await Promise.all([
        api.get('/applications/my'),
        api.get('/contracts/my'),
        api.get('/payments/my')
      ]);
      setApplications(apps.data || []);
      setContracts(contrs.data || []);
      setPayments(pays.data || []);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });
    
    try {
      const response = await api.put('/users/me', formData);
      updateUser(response.data);
      setMessage({ type: 'success', text: 'Профиль успешно обновлён' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Ошибка обновления' });
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'Пароли не совпадают' });
      return;
    }
    if (passwordData.new_password.length < 6) {
      setMessage({ type: 'error', text: 'Пароль должен быть не менее 6 символов' });
      return;
    }
    
    setLoading(true);
    try {
      await api.put('/users/me', { password: passwordData.new_password });
      setPasswordData({ new_password: '', confirm_password: '' });
      setMessage({ type: 'success', text: 'Пароль успешно изменён' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Ошибка смены пароля' });
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (statusName) => {
    const name = statusName?.toLowerCase() || '';
    if (name === 'новая' || name === 'new') return 'status-new';
    if (name === 'одобрена' || name === 'approved') return 'status-approved';
    if (name === 'отказана' || name === 'rejected') return 'status-rejected';
    if (name === 'действует' || name === 'active') return 'status-active';
    return '';
  };

  const getStatusText = (statusName) => {
    const name = statusName?.toLowerCase() || '';
    const map = {
      'new': 'Новая', 'approved': 'Одобрена', 'rejected': 'Отказана',
      'active': 'Действует', 'expired': 'Истек',
      'paid': 'Оплачено', 'overdue': 'Просрочено'
    };
    return map[name] || statusName || '—';
  };

  const isClient = user?.role_id === 3;
  const isManager = user?.role_id === 2;
  const isAdmin = user?.role_id === 1;

  return (
    <div className="profile-container">
      <div className="profile-header">
        <UserCircle size={48} />
        <div>
          <h1>Личный кабинет</h1>
          <p>{user?.login} • {isClient ? 'Клиент' : isManager ? 'Менеджер' : 'Администратор'}</p>
        </div>
      </div>

      {message.text && (
        <div className={`profile-message ${message.type}`}>{message.text}</div>
      )}

      <div className="profile-tabs">
        <button className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`} onClick={() => setActiveTab('profile')}>
          <User size={16} /> Профиль
        </button>
        <button className={`tab-btn ${activeTab === 'security' ? 'active' : ''}`} onClick={() => setActiveTab('security')}>
          <Lock size={16} /> Безопасность
        </button>
        {isClient && (
          <>
            <button className={`tab-btn ${activeTab === 'applications' ? 'active' : ''}`} onClick={() => setActiveTab('applications')}>
              <FileText size={16} /> Заявки
            </button>
            <button className={`tab-btn ${activeTab === 'contracts' ? 'active' : ''}`} onClick={() => setActiveTab('contracts')}>
              <FileCheck size={16} /> Договоры
            </button>
            <button className={`tab-btn ${activeTab === 'payments' ? 'active' : ''}`} onClick={() => setActiveTab('payments')}>
              <CreditCard size={16} /> Платежи
            </button>
          </>
        )}
      </div>

      <div className="profile-content">
        {/* Вкладка Профиль */}
        {activeTab === 'profile' && (
          <div className="profile-card">
            <h2>Основная информация</h2>
            <form onSubmit={handleUpdateProfile}>
              <div className="form-group">
                <label><User size={16} /> ФИО</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="Введите ваше имя"
                />
              </div>
              <div className="form-group">
                <label><Phone size={16} /> Телефон</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+7 (___) ___-__-__"
                />
              </div>
              <div className="form-group">
                <label><Mail size={16} /> Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <button type="submit" className="profile-btn" disabled={loading}>
                <Save size={16} /> Сохранить изменения
              </button>
            </form>
          </div>
        )}

        {/* Вкладка Безопасность */}
        {activeTab === 'security' && (
          <div className="profile-card">
            <h2>Смена пароля</h2>
            <form onSubmit={handleChangePassword}>
              <div className="form-group">
                <label><Lock size={16} /> Новый пароль</label>
                <input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  required
                  minLength={6}
                />
              </div>
              <div className="form-group">
                <label><Lock size={16} /> Подтвердите пароль</label>
                <input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  required
                />
              </div>
              <button type="submit" className="profile-btn" disabled={loading}>
                <Save size={16} /> Сменить пароль
              </button>
            </form>
          </div>
        )}

        {/* Вкладка Заявки (только для клиента) */}
        {activeTab === 'applications' && isClient && (
          <div className="profile-card">
            <h2>Мои заявки</h2>
            {applications.length === 0 ? (
              <p className="empty-data">Нет заявок</p>
            ) : (
              <div className="data-table">
                <table>
                  <thead>
                    <tr><th>Офис</th><th>Дата</th><th>Статус</th></tr>
                  </thead>
                  <tbody>
                    {applications.map(app => (
                      <tr key={app.id}>
                        <td>Офис {app.office_number}</td>
                        <td>{app.created_at?.split('T')[0]}</td>
                        <td><span className={`status-badge ${getStatusBadge(app.status_name)}`}>{getStatusText(app.status_name)}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Вкладка Договоры (только для клиента) */}
        {activeTab === 'contracts' && isClient && (
          <div className="profile-card">
            <h2>Мои договоры</h2>
            {contracts.length === 0 ? (
              <p className="empty-data">Нет договоров</p>
            ) : (
              <div className="data-table">
                <table>
                  <thead>
                    <tr><th>Офис</th><th>Период</th><th>Сумма</th><th>Статус</th></tr>
                  </thead>
                  <tbody>
                    {contracts.map(contract => (
                      <tr key={contract.id}>
                        <td>Офис {contract.office_number}</td>
                        <td>{contract.start_date} — {contract.end_date}</td>
                        <td>{contract.total_amount?.toLocaleString()} ₽</td>
                        <td><span className={`status-badge ${getStatusBadge(contract.status_name)}`}>{getStatusText(contract.status_name)}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Вкладка Платежи (только для клиента) */}
        {activeTab === 'payments' && isClient && (
          <div className="profile-card">
            <h2>Мои платежи</h2>
            {payments.length === 0 ? (
              <p className="empty-data">Нет платежей</p>
            ) : (
              <div className="data-table">
                <table>
                  <thead>
                    <tr><th>Сумма</th><th>Дата</th><th>Статус</th></tr>
                  </thead>
                  <tbody>
                    {payments.map(payment => (
                      <tr key={payment.id}>
                        <td>{payment.amount?.toLocaleString()} ₽</td>
                        <td>{payment.payment_date}</td>
                        <td><span className={`status-badge ${getStatusBadge(payment.status_name)}`}>{getStatusText(payment.status_name)}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;