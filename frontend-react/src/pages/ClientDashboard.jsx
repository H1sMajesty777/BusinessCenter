import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import '../styles/clientDashboard.css';

const ClientDashboard = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('applications');
  const [applications, setApplications] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState({
    applications: true,
    contracts: true,
    payments: true
  });

  // Загрузка заявок
  useEffect(() => {
    if (activeTab === 'applications') {
      loadApplications();
    }
  }, [activeTab]);

  useEffect(() => {
    loadContracts();
    loadPayments();
  }, []);

  const loadApplications = async () => {
    setLoading(prev => ({ ...prev, applications: true }));
    try {
      const response = await api.get('/applications?user_id=' + user?.id);
      setApplications(response.data || []);
    } catch (error) {
      console.error('Ошибка загрузки заявок:', error);
      // Мок-данные для демонстрации
      setApplications([
        {
          id: 1,
          office_number: '101',
          status_id: 1,
          status_name: 'Новая',
          desired_date: '2026-04-25',
          created_at: '2026-04-18'
        },
        {
          id: 2,
          office_number: '205',
          status_id: 2,
          status_name: 'Одобрена',
          desired_date: '2026-04-20',
          created_at: '2026-04-15'
        }
      ]);
    } finally {
      setLoading(prev => ({ ...prev, applications: false }));
    }
  };

  const loadContracts = async () => {
    setLoading(prev => ({ ...prev, contracts: true }));
    try {
      const response = await api.get('/contracts/my');
      setContracts(response.data || []);
    } catch (error) {
      console.error('Ошибка загрузки договоров:', error);
      // Мок-данные для демонстрации
      setContracts([
        {
          id: 1,
          office_number: '101',
          start_date: '2026-01-01',
          end_date: '2026-12-31',
          total_amount: 540000,
          status_name: 'Действует'
        }
      ]);
    } finally {
      setLoading(prev => ({ ...prev, contracts: false }));
    }
  };

  const loadPayments = async () => {
    setLoading(prev => ({ ...prev, payments: true }));
    try {
      const response = await api.get('/payments/my');
      setPayments(response.data || []);
    } catch (error) {
      console.error('Ошибка загрузки платежей:', error);
      // Мок-данные для демонстрации
      setPayments([
        {
          id: 1,
          office_number: '101',
          amount: 45000,
          payment_date: '2026-01-05',
          status_name: 'Оплачено'
        },
        {
          id: 2,
          office_number: '101',
          amount: 45000,
          payment_date: '2026-02-05',
          status_name: 'Оплачено'
        },
        {
          id: 3,
          office_number: '101',
          amount: 45000,
          payment_date: '2026-03-05',
          status_name: 'Просрочено'
        }
      ]);
    } finally {
      setLoading(prev => ({ ...prev, payments: false }));
    }
  };

  const getStatusClass = (statusName) => {
    const map = {
      'Новая': 'status-new',
      'Одобрена': 'status-approved',
      'Отказана': 'status-rejected',
      'Договор заключён': 'status-contract',
      'Действует': 'status-active',
      'Истек': 'status-expired',
      'Оплачено': 'status-paid',
      'Просрочено': 'status-overdue'
    };
    return map[statusName] || 'status-new';
  };

  // Рендер таблицы заявок
  const renderApplications = () => {
    if (loading.applications) {
      return <div className="loading-state">Загрузка заявок...</div>;
    }
    
    if (applications.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <div className="empty-title">Нет заявок</div>
          <div className="empty-text">Вы ещё не оставляли заявки на офисы</div>
        </div>
      );
    }
    
    return (
      <table className="data-table">
        <thead>
          <tr>
            <th>Офис</th>
            <th>Дата создания</th>
            <th>Желаемая дата</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          {applications.map(app => (
            <tr key={app.id}>
              <td>Офис {app.office_number}</td>
              <td>{app.created_at}</td>
              <td>{app.desired_date}</td>
              <td>
                <span className={`status-badge ${getStatusClass(app.status_name)}`}>
                  {app.status_name}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  // Рендер таблицы договоров
  const renderContracts = () => {
    if (loading.contracts) {
      return <div className="loading-state">Загрузка договоров...</div>;
    }
    
    if (contracts.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">📄</div>
          <div className="empty-title">Нет договоров</div>
          <div className="empty-text">У вас пока нет заключённых договоров</div>
        </div>
      );
    }
    
    return (
      <table className="data-table">
        <thead>
          <tr>
            <th>Офис</th>
            <th>Дата начала</th>
            <th>Дата окончания</th>
            <th>Сумма</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          {contracts.map(contract => (
            <tr key={contract.id}>
              <td>Офис {contract.office_number}</td>
              <td>{contract.start_date}</td>
              <td>{contract.end_date}</td>
              <td>{contract.total_amount?.toLocaleString()} ₽</td>
              <td>
                <span className={`status-badge ${getStatusClass(contract.status_name)}`}>
                  {contract.status_name}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  // Рендер таблицы платежей
  const renderPayments = () => {
    if (loading.payments) {
      return <div className="loading-state">Загрузка платежей...</div>;
    }
    
    if (payments.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">💰</div>
          <div className="empty-title">Нет платежей</div>
          <div className="empty-text">История платежей пуста</div>
        </div>
      );
    }
    
    return (
      <table className="data-table">
        <thead>
          <tr>
            <th>Офис</th>
            <th>Сумма</th>
            <th>Дата платежа</th>
            <th>Статус</th>
           </tr>
        </thead>
        <tbody>
          {payments.map(payment => (
            <tr key={payment.id}>
              <td>Офис {payment.office_number}</td>
              <td>{payment.amount?.toLocaleString()} ₽</td>
              <td>{payment.payment_date}</td>
              <td>
                <span className={`status-badge ${getStatusClass(payment.status_name)}`}>
                  {payment.status_name}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  // Получаем имя пользователя
  const userName = user?.full_name || user?.login || 'Клиент';
  const firstName = userName.split(' ')[0];

  return (
    <div className="client-dashboard">
      <div className="welcome-section">
        <h1 className="welcome-title">Здравствуйте, {firstName}!</h1>
        <p className="welcome-subtitle">Добро пожаловать в личный кабинет</p>
      </div>
      
      <div className="dashboard-tabs">
        <button
          className={`tab-btn ${activeTab === 'applications' ? 'active' : ''}`}
          onClick={() => setActiveTab('applications')}
        >
          📋 Мои заявки
        </button>
        <button
          className={`tab-btn ${activeTab === 'contracts' ? 'active' : ''}`}
          onClick={() => setActiveTab('contracts')}
        >
          📄 Мои договоры
        </button>
        <button
          className={`tab-btn ${activeTab === 'payments' ? 'active' : ''}`}
          onClick={() => setActiveTab('payments')}
        >
          💰 Мои платежи
        </button>
      </div>
      
      <div className="table-container">
        {activeTab === 'applications' && renderApplications()}
        {activeTab === 'contracts' && renderContracts()}
        {activeTab === 'payments' && renderPayments()}
      </div>
    </div>
  );
};

export default ClientDashboard;