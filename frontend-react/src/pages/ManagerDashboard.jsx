// frontend/src/pages/ManagerDashboard.jsx

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { 
  FileText, FileCheck, CheckCircle, XCircle, Clock, 
  Eye, Bell, Calendar, User as UserIcon, Building2, 
  DollarSign, MessageSquare, Phone, Mail, Send, 
  RefreshCw, ChevronDown, ChevronUp, Copy, Check,
  TrendingUp, TrendingDown, AlertCircle, Archive, Star
} from 'lucide-react';
import '../styles/managerDashboard.css';

const ManagerDashboard = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('applications');
  const [applications, setApplications] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedContract, setSelectedContract] = useState(null);
  const [showContractModal, setShowContractModal] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [showAppModal, setShowAppModal] = useState(false);
  const [userContacts, setUserContacts] = useState(null);
  const [newApplicationsCount, setNewApplicationsCount] = useState(0);
  const [statusChangeLoading, setStatusChangeLoading] = useState(false);
  const [copiedField, setCopiedField] = useState(null);

  // Статусы заявок
  const statuses = [
    { id: 1, name: 'Новая', icon: <Bell size={14} />, color: '#fef3c7', textColor: '#92400e', borderColor: '#fde68a', order: 1 },
    { id: 2, name: 'Одобрена', icon: <CheckCircle size={14} />, color: '#dcfce7', textColor: '#166534', borderColor: '#bbf7d0', order: 2 },
    { id: 3, name: 'Отказана', icon: <XCircle size={14} />, color: '#fee2e2', textColor: '#991b1b', borderColor: '#fecaca', order: 3 }
  ];

  useEffect(() => {
    loadApplications();
    loadContracts();
    
    const interval = setInterval(() => {
      loadApplications();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const newCount = applications.filter(app => app.status_id === 1).length;
    setNewApplicationsCount(newCount);
    
    if (newCount > 0) {
      document.title = `(${newCount}) Управление - Business Center`;
    } else {
      document.title = 'Управление - Business Center';
    }
  }, [applications]);

  const loadApplications = async () => {
    try {
      const response = await api.get('/applications');
      const apps = response.data || [];
      
      // Сортировка по статусу (1 → 2 → 3) и по дате внутри группы
      const sorted = apps.sort((a, b) => {
        if (a.status_id !== b.status_id) return a.status_id - b.status_id;
        return new Date(b.created_at) - new Date(a.created_at);
      });
      
      setApplications(sorted);
    } catch (error) {
      console.error('Ошибка загрузки заявок:', error);
    }
  };

  const loadContracts = async () => {
    try {
      const response = await api.get('/contracts');
      setContracts(response.data || []);
    } catch (error) {
      console.error('Ошибка загрузки договоров:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserContacts = async (userId) => {
    try {
      const response = await api.get(`/users/${userId}/contacts`);
      setUserContacts(response.data);
    } catch (error) {
      console.error('Ошибка загрузки контактов:', error);
      setUserContacts(null);
    }
  };

  const updateApplicationStatus = async (appId, statusId) => {
    setStatusChangeLoading(true);
    try {
      await api.put(`/applications/${appId}/status`, { status_id: statusId });
      await loadApplications();
      
      if (selectedApplication?.id === appId) {
        setShowAppModal(false);
        setSelectedApplication(null);
        setUserContacts(null);
      }
      
      const status = statuses.find(s => s.id === statusId);
      alert(`✅ Заявка ${status?.name || 'обновлена'}`);
    } catch (error) {
      console.error('Ошибка обновления:', error);
      alert('❌ Ошибка при обновлении статуса');
    } finally {
      setStatusChangeLoading(false);
    }
  };

  const getStatusConfig = (statusId) => {
    return statuses.find(s => s.id === statusId) || statuses[0];
  };

  const handleViewApplication = async (app) => {
    setSelectedApplication(app);
    await loadUserContacts(app.user_id);
    setShowAppModal(true);
  };

  const handleViewContract = (contract) => {
    setSelectedContract(contract);
    setShowContractModal(true);
  };

  const handleCopyToClipboard = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Ошибка копирования:', err);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRelativeTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'только что';
    if (diffMins < 60) return `${diffMins} мин назад`;
    if (diffHours < 24) return `${diffHours} ч назад`;
    return `${diffDays} д назад`;
  };

  const getStatusButtonClass = (statusId, currentStatusId) => {
    if (statusId === currentStatusId) return 'active';
    if (statusId === 1 && currentStatusId !== 1) return 'to-new';
    if (statusId === 2 && currentStatusId !== 2) return 'to-approved';
    if (statusId === 3 && currentStatusId !== 3) return 'to-rejected';
    return '';
  };

  return (
    <div className="manager-dashboard">
      {/* Герой-секция */}
      <div className="hero-section">
        <div className="hero-content">
          <div className="hero-icon">
            <FileText size={32} />
          </div>
          <div>
            <h1 className="hero-title">Панель управления</h1>
            <p className="hero-subtitle">Управление заявками и договорами аренды</p>
          </div>
        </div>
        
        {newApplicationsCount > 0 && (
          <div className="notification-pulse">
            <div className="pulse-ring"></div>
            <div className="notification-badge">
              <Bell size={18} />
              <span className="notification-count">{newApplicationsCount}</span>
              <span className="notification-text">новых заявок</span>
            </div>
          </div>
        )}
      </div>

      {/* Вкладки */}
      <div className="tabs-container">
        <button 
          className={`tab-btn ${activeTab === 'applications' ? 'active' : ''}`} 
          onClick={() => setActiveTab('applications')}
        >
          <FileText size={18} />
          Заявки
          {newApplicationsCount > 0 && (
            <span className="tab-badge">{newApplicationsCount}</span>
          )}
        </button>
        <button 
          className={`tab-btn ${activeTab === 'contracts' ? 'active' : ''}`} 
          onClick={() => setActiveTab('contracts')}
        >
          <FileCheck size={18} />
          Договоры
          <span className="tab-count">{contracts.length}</span>
        </button>
      </div>

      {/* Секция заявок */}
      {activeTab === 'applications' && (
        <div className="applications-section">
          <div className="section-header">
            <h2>
              <MessageSquare size={20} />
              Все заявки
            </h2>
            <div className="stats-badge">
              <span className="stat-new">{applications.filter(a => a.status_id === 1).length} новых</span>
              <span className="stat-approved">{applications.filter(a => a.status_id === 2).length} одобренных</span>
              <span className="stat-rejected">{applications.filter(a => a.status_id === 3).length} отклонённых</span>
            </div>
          </div>
          
          {loading ? (
            <div className="loading-state">
              <RefreshCw size={32} className="spinning" />
              <p>Загрузка заявок...</p>
            </div>
          ) : applications.length === 0 ? (
            <div className="empty-state">
              <Archive size={48} />
              <h3>Нет заявок</h3>
              <p>Новые заявки будут появляться здесь</p>
            </div>
          ) : (
            <div className="applications-grid">
              {applications.map(app => {
                const status = getStatusConfig(app.status_id);
                const isNew = app.status_id === 1;
                const relativeTime = getRelativeTime(app.created_at);
                
                return (
                  <div 
                    key={app.id} 
                    className={`application-card status-${app.status_id}`}
                    onClick={() => handleViewApplication(app)}
                  >
                    <div className="card-header">
                      <div className="card-badges">
                        <span 
                          className="status-chip"
                          style={{ background: status.color, color: status.textColor }}
                        >
                          {status.icon}
                          {status.name}
                        </span>
                        {isNew && (
                          <span className="new-chip">
                            <Bell size={10} />
                            NEW
                          </span>
                        )}
                      </div>
                      <div className="card-time">
                        <Clock size={12} />
                        <span>{relativeTime}</span>
                      </div>
                    </div>
                    
                    <div className="card-body">
                      <div className="info-row">
                        <Building2 size={16} />
                        <span className="info-label">Офис</span>
                        <span className="info-value">№{app.office_number}</span>
                      </div>
                      <div className="info-row">
                        <UserIcon size={16} />
                        <span className="info-label">Клиент</span>
                        <span className="info-value">{app.user_login}</span>
                      </div>
                      {app.comment && (
                        <div className="comment-preview">
                          <MessageSquare size={14} />
                          <span>{app.comment.length > 60 ? app.comment.slice(0, 60) + '...' : app.comment}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="card-footer">
                      <button className="detail-btn">
                        <Eye size={16} />
                        Подробнее
                        <ChevronDown size={14} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Секция договоров */}
      {activeTab === 'contracts' && (
        <div className="contracts-section">
          <div className="section-header">
            <h2>
              <FileCheck size={20} />
              Все договоры
            </h2>
            <div className="stats-badge">
              <span className="stat-total">Всего: {contracts.length}</span>
              <span className="stat-active">Действует: {contracts.filter(c => c.status_name === 'Действует').length}</span>
            </div>
          </div>
          
          <div className="contracts-grid">
            {contracts.length === 0 ? (
              <div className="empty-state">
                <FileCheck size={48} />
                <h3>Нет договоров</h3>
                <p>Договоры появятся после одобрения заявок</p>
              </div>
            ) : (
              contracts.map(contract => {
                const isActive = contract.status_name === 'Действует';
                return (
                  <div 
                    key={contract.id} 
                    className={`contract-card ${isActive ? 'active' : 'expired'}`}
                    onClick={() => handleViewContract(contract)}
                  >
                    <div className="contract-card-header">
                      <div className="office-badge">
                        <Building2 size={16} />
                        <span>Офис {contract.office_number}</span>
                      </div>
                      <span className={`contract-status ${isActive ? 'active' : 'expired'}`}>
                        {isActive ? 'Действует' : 'Завершён'}
                      </span>
                    </div>
                    
                    <div className="contract-card-body">
                      <div className="info-row">
                        <UserIcon size={14} />
                        <span className="info-label">Арендатор</span>
                        <span className="info-value">{contract.user_login}</span>
                      </div>
                      <div className="info-row">
                        <Calendar size={14} />
                        <span className="info-label">Период</span>
                        <span className="info-value">{contract.start_date} — {contract.end_date}</span>
                      </div>
                      <div className="info-row highlight">
                        <DollarSign size={14} />
                        <span className="info-label">Сумма</span>
                        <span className="info-value amount">{contract.total_amount?.toLocaleString()} ₽</span>
                      </div>
                    </div>
                    
                    <div className="contract-card-footer">
                      <button className="detail-btn">
                        <Eye size={16} />
                        Детали договора
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Модальное окно заявки */}
      {showAppModal && selectedApplication && (
        <div className="modal-overlay" onClick={() => setShowAppModal(false)}>
          <div className="modal-content application-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                <div className="title-icon">
                  <MessageSquare size={20} />
                </div>
                <div>
                  <h3>Заявка #{selectedApplication.id}</h3>
                  <p className="modal-subtitle">от {formatDate(selectedApplication.created_at)}</p>
                </div>
              </div>
              <button className="close-modal" onClick={() => setShowAppModal(false)}>
                <XCircle size={22} />
              </button>
            </div>
            
            <div className="modal-body">
              {/* Секция информации */}
              <div className="detail-section">
                <h4>
                  <Building2 size={16} />
                  Информация о заявке
                </h4>
                <div className="info-grid">
                  <div className="info-item">
                    <label>Офис</label>
                    <span>№{selectedApplication.office_number}</span>
                  </div>
                  <div className="info-item">
                    <label>Клиент</label>
                    <span>{selectedApplication.user_login}</span>
                  </div>
                  <div className="info-item">
                    <label>Дата создания</label>
                    <span>{formatDate(selectedApplication.created_at)}</span>
                  </div>
                  {selectedApplication.reviewed_at && (
                    <div className="info-item">
                      <label>Дата обработки</label>
                      <span>{formatDate(selectedApplication.reviewed_at)}</span>
                    </div>
                  )}
                  <div className="info-item full-width">
                    <label>Комментарий</label>
                    <div className="comment-box">
                      {selectedApplication.comment || 'Нет комментария'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Секция контактов */}
              <div className="detail-section contacts-section">
                <h4>
                  <Phone size={16} />
                  Контакты клиента
                </h4>
                {userContacts ? (
                  <div className="contacts-container">
                    <div className="contact-item">
                      <div className="contact-icon phone">
                        <Phone size={16} />
                      </div>
                      <div className="contact-info">
                        <span className="contact-label">Телефон</span>
                        <span className="contact-value">{userContacts.phone || 'Не указан'}</span>
                      </div>
                      {userContacts.phone && (
                        <div className="contact-actions">
                          <a href={`tel:${userContacts.phone}`} className="contact-action call" title="Позвонить">
                            <Phone size={16} />
                          </a>
                          <button 
                            className="contact-action copy" 
                            onClick={() => handleCopyToClipboard(userContacts.phone, 'phone')}
                            title="Копировать"
                          >
                            {copiedField === 'phone' ? <Check size={16} /> : <Copy size={16} />}
                          </button>
                        </div>
                      )}
                    </div>
                    <div className="contact-item">
                      <div className="contact-icon email">
                        <Mail size={16} />
                      </div>
                      <div className="contact-info">
                        <span className="contact-label">Email</span>
                        <span className="contact-value">{userContacts.email || 'Не указан'}</span>
                      </div>
                      {userContacts.email && (
                        <div className="contact-actions">
                          <a href={`mailto:${userContacts.email}`} className="contact-action email" title="Написать">
                            <Mail size={16} />
                          </a>
                          <button 
                            className="contact-action copy" 
                            onClick={() => handleCopyToClipboard(userContacts.email, 'email')}
                            title="Копировать"
                          >
                            {copiedField === 'email' ? <Check size={16} /> : <Copy size={16} />}
                          </button>
                        </div>
                      )}
                    </div>
                    <div className="contact-note">
                      <AlertCircle size={12} />
                      <span>Нажмите на иконку телефона — откроется приложение для звонков</span>
                    </div>
                  </div>
                ) : (
                  <div className="loading-contacts">
                    <RefreshCw size={20} className="spinning" />
                    <span>Загрузка контактов...</span>
                  </div>
                )}
              </div>

              {/* Секция изменения статуса */}
              <div className="detail-section status-section">
                <h4>
                  <Star size={16} />
                  Изменить статус
                </h4>
                <div className="status-buttons">
                  {statuses.map(status => (
                    <button
                      key={status.id}
                      className={`status-change-btn ${getStatusButtonClass(status.id, selectedApplication.status_id)}`}
                      onClick={() => updateApplicationStatus(selectedApplication.id, status.id)}
                      disabled={statusChangeLoading || selectedApplication.status_id === status.id}
                    >
                      {status.icon}
                      {status.name}
                      {selectedApplication.status_id === status.id && <CheckCircle size={12} />}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="modal-footer">
              {selectedApplication.status_id === 1 && (
                <button 
                  className="footer-btn approve"
                  onClick={() => updateApplicationStatus(selectedApplication.id, 2)}
                >
                  <CheckCircle size={16} />
                  Одобрить заявку
                </button>
              )}
              <button className="footer-btn secondary" onClick={() => setShowAppModal(false)}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно договора */}
      {showContractModal && selectedContract && (
        <div className="modal-overlay" onClick={() => setShowContractModal(false)}>
          <div className="modal-content contract-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                <div className="title-icon contract">
                  <FileCheck size={20} />
                </div>
                <div>
                  <h3>Договор аренды</h3>
                  <p className="modal-subtitle">№{selectedContract.id}</p>
                </div>
              </div>
              <button className="close-modal" onClick={() => setShowContractModal(false)}>
                <XCircle size={22} />
              </button>
            </div>
            
            <div className="modal-body">
              <div className="detail-section">
                <h4>Основная информация</h4>
                <div className="info-grid">
                  <div className="info-item">
                    <label>Офис</label>
                    <span>№{selectedContract.office_number}</span>
                  </div>
                  <div className="info-item">
                    <label>Арендатор</label>
                    <span>{selectedContract.user_login}</span>
                  </div>
                  <div className="info-item">
                    <label>Начало аренды</label>
                    <span>{selectedContract.start_date}</span>
                  </div>
                  <div className="info-item">
                    <label>Окончание</label>
                    <span>{selectedContract.end_date}</span>
                  </div>
                  <div className="info-item full-width">
                    <label>Общая сумма</label>
                    <span className="total-amount">{selectedContract.total_amount?.toLocaleString()} ₽</span>
                  </div>
                  <div className="info-item">
                    <label>Дата подписания</label>
                    <span>{selectedContract.signed_at?.split('T')[0] || '—'}</span>
                  </div>
                  <div className="info-item">
                    <label>Статус</label>
                    <span className={`contract-status-badge ${selectedContract.status_name === 'Действует' ? 'active' : 'expired'}`}>
                      {selectedContract.status_name}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="footer-btn secondary" onClick={() => setShowContractModal(false)}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManagerDashboard;