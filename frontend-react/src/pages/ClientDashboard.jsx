import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useFavorites } from '../contexts/FavoritesContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { getOfficeImages } from '../utils/mockImages';
import ImageSlider from '../components/ImageSlider';
import { 
  User, FileText, FileCheck, CreditCard, Heart,
  Calendar, Clock, CheckCircle, XCircle, AlertCircle,
  Building2, Ruler, DollarSign, MapPin, Eye, Trash2
} from 'lucide-react';
import '../styles/clientDashboard.css';

const ClientDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { favorites, removeFromFavorites } = useFavorites();
  const [activeTab, setActiveTab] = useState('applications');
  const [applications, setApplications] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState({
    applications: true,
    contracts: true,
    payments: true
  });

  useEffect(() => {
    loadApplications();
    loadContracts();
    loadPayments();
  }, []);

  const loadApplications = async () => {
    setLoading(prev => ({ ...prev, applications: true }));
    try {
      const response = await api.get('/applications/my');
      setApplications(response.data || []);
    } catch (error) {
      console.error('Ошибка загрузки заявок:', error);
      setApplications([]);
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
      setContracts([]);
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
      setPayments([]);
    } finally {
      setLoading(prev => ({ ...prev, payments: false }));
    }
  };

  const handleOfficeClick = (id) => {
    navigate(`/office/${id}`);
  };

  const handleRemoveFromFavorites = (office, e) => {
    e.stopPropagation();
    removeFromFavorites(office.id);
  };

  const getStatusIcon = (statusName) => {
    const name = statusName?.toLowerCase() || '';
    if (name === 'новая' || name === 'new') return <Clock size={14} style={{ marginRight: '4px' }} />;
    if (name === 'одобрена' || name === 'approved') return <CheckCircle size={14} style={{ marginRight: '4px' }} />;
    if (name === 'отказана' || name === 'rejected') return <XCircle size={14} style={{ marginRight: '4px' }} />;
    if (name === 'действует' || name === 'active') return <FileCheck size={14} style={{ marginRight: '4px' }} />;
    if (name === 'истек' || name === 'expired') return <AlertCircle size={14} style={{ marginRight: '4px' }} />;
    if (name === 'оплачено' || name === 'paid') return <CheckCircle size={14} style={{ marginRight: '4px' }} />;
    if (name === 'просрочено' || name === 'overdue') return <AlertCircle size={14} style={{ marginRight: '4px' }} />;
    return null;
  };

  const getStatusClass = (statusName) => {
    const name = statusName?.toLowerCase() || '';
    const map = {
      'новая': 'status-new', 'new': 'status-new',
      'одобрена': 'status-approved', 'approved': 'status-approved',
      'отказана': 'status-rejected', 'rejected': 'status-rejected',
      'действует': 'status-active', 'active': 'status-active',
      'истек': 'status-expired', 'expired': 'status-expired',
      'оплачено': 'status-paid', 'paid': 'status-paid',
      'просрочено': 'status-overdue', 'overdue': 'status-overdue'
    };
    return map[name] || 'status-new';
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

  const userName = user?.full_name || user?.login || 'Клиент';
  const firstName = userName.split(' ')[0];

  const renderFavorites = () => {
    if (favorites.length === 0) {
      return (
        <div className="empty-state">
          <Heart size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
          <div className="empty-title">Нет избранных офисов</div>
          <div className="empty-text">Добавляйте офисы в избранное на главной странице</div>
        </div>
      );
    }

    return (
      <div className="favorites-grid">
        {favorites.map(office => {
          const images = getOfficeImages(office.id);
          return (
            <div 
              key={office.id} 
              className="favorite-card"
              onClick={() => handleOfficeClick(office.id)}
            >
              <ImageSlider 
                images={images} 
                officeNumber={office.office_number}
                className="medium"
              />
              <div className="office-content">
                <div className="office-header">
                  <h3 className="office-number">Офис {office.office_number}</h3>
                  <span className="office-floor">
                    <MapPin size={14} style={{ marginRight: '4px' }} />
                    {office.floor} этаж
                  </span>
                </div>
                <div className="office-details-small">
                  <div className="detail-item">
                    <Ruler size={16} />
                    <div className="detail-label">Площадь</div>
                    <div className="detail-value">{office.area_sqm} м²</div>
                  </div>
                  <div className="detail-item">
                    <DollarSign size={16} />
                    <div className="detail-label">Цена</div>
                    <div className="detail-value">{office.price_per_month.toLocaleString()} ₽</div>
                  </div>
                </div>
                <div className="office-actions-small">
                  <button className="btn-details-small" onClick={() => handleOfficeClick(office.id)}>
                    <Eye size={16} style={{ marginRight: '6px' }} />
                    Подробнее
                  </button>
                  <button 
                    className="btn-remove-small"
                    onClick={(e) => handleRemoveFromFavorites(office, e)}
                  >
                    <Trash2 size={16} style={{ marginRight: '6px' }} />
                    Удалить
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="client-dashboard">
      <div className="welcome-section">
        <h1 className="welcome-title">
          <User size={28} style={{ marginRight: '12px', verticalAlign: 'middle' }} />
          Здравствуйте, {firstName}!
        </h1>
        <p className="welcome-subtitle">Добро пожаловать в личный кабинет</p>
      </div>
      
      <div className="dashboard-tabs">
        <button className={`tab-btn ${activeTab === 'applications' ? 'active' : ''}`} onClick={() => setActiveTab('applications')}>
          <FileText size={16} style={{ marginRight: '8px' }} />
          Мои заявки
        </button>
        <button className={`tab-btn ${activeTab === 'contracts' ? 'active' : ''}`} onClick={() => setActiveTab('contracts')}>
          <FileCheck size={16} style={{ marginRight: '8px' }} />
          Мои договоры
        </button>
        <button className={`tab-btn ${activeTab === 'payments' ? 'active' : ''}`} onClick={() => setActiveTab('payments')}>
          <CreditCard size={16} style={{ marginRight: '8px' }} />
          Мои платежи
        </button>
        <button className={`tab-btn ${activeTab === 'favorites' ? 'active' : ''}`} onClick={() => setActiveTab('favorites')}>
          <Heart size={16} style={{ marginRight: '8px' }} />
          Избранное
        </button>
      </div>
      
      <div className="table-container">
        {activeTab === 'applications' && (
          loading.applications ? <div className="loading-state">Загрузка...</div> :
          applications.length === 0 ? <div className="empty-state"><FileText size={48} /><div>Нет заявок</div></div> :
          <table className="data-table">
            <thead>
              <tr>
                <th>Офис</th>
                <th>Дата создания</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {applications.map(app => (
                <tr key={app.id}>
                  <td><strong>Офис {app.office_number || app.office_id}</strong></td>
                  <td>{app.created_at?.split('T')[0]}</td>
                  <td>
                    <span className={`status-badge ${getStatusClass(app.status_name)}`}>
                      {getStatusIcon(app.status_name)}{getStatusText(app.status_name)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {activeTab === 'contracts' && (
          loading.contracts ? <div className="loading-state">Загрузка...</div> :
          contracts.length === 0 ? <div className="empty-state"><FileCheck size={48} /><div>Нет договоров</div></div> :
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
              {contracts.map(c => (
                <tr key={c.id}>
                  <td><strong>Офис {c.office_number || c.office_id}</strong></td>
                  <td>{c.start_date}</td>
                  <td>{c.end_date}</td>
                  <td>{c.total_amount?.toLocaleString()} ₽</td>
                  <td>
                    <span className={`status-badge ${getStatusClass(c.status_name)}`}>
                      {getStatusIcon(c.status_name)}{getStatusText(c.status_name)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {activeTab === 'payments' && (
          loading.payments ? <div className="loading-state">Загрузка...</div> :
          payments.length === 0 ? <div className="empty-state"><CreditCard size={48} /><div>Нет платежей</div></div> :
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
              {payments.map(p => (
                <tr key={p.id}>
                  <td><strong>Офис {p.office_number || p.contract_id}</strong></td>
                  <td>{p.amount?.toLocaleString()} ₽</td>
                  <td>{p.payment_date}</td>
                  <td>
                    <span className={`status-badge ${getStatusClass(p.status_name)}`}>
                      {getStatusIcon(p.status_name)}{getStatusText(p.status_name)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {activeTab === 'favorites' && renderFavorites()}
      </div>
    </div>
  );
};

export default ClientDashboard;