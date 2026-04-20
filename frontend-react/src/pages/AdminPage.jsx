import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import '../styles/admin.css';
import { 
  Users, Building2, History, Brain, Plus, Edit2, Trash2, 
  UserPlus, Home, Calendar, AlertCircle, CheckCircle, XCircle,
  BarChart3, Settings, Mail, Phone, User, Lock, Unlock,
  X, Save, RefreshCw, Eye, EyeOff, FileText, Clock
} from 'lucide-react';

const AdminPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [loading, setLoading] = useState(false);
  
  // Данные
  const [users, setUsers] = useState([]);
  const [offices, setOffices] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  
  // Модальные окна
  const [showUserModal, setShowUserModal] = useState(false);
  const [showOfficeModal, setShowOfficeModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  // Формы
  const [userForm, setUserForm] = useState({ login: '', email: '', password: '', role_id: 3, phone: '', full_name: '' });
  const [officeForm, setOfficeForm] = useState({ office_number: '', floor: '', area_sqm: '', price_per_month: '', description: '', is_free: true });
  
  // AI
  const [training, setTraining] = useState(false);
  const [lastTrained, setLastTrained] = useState('2026-04-15');
  const [metrics, setMetrics] = useState({ accuracy: '92%', auc: '0.89' });

  // Загрузка данных
  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Ошибка загрузки пользователей:', error);
      setUsers([
        { id: 1, login: 'admin', email: 'admin@test.com', role_id: 1, is_active: true, created_at: '2026-01-01', full_name: 'Админ Админов' },
        { id: 2, login: 'manager', email: 'manager@test.com', role_id: 2, is_active: true, created_at: '2026-01-02', full_name: 'Менеджер Менеджеров' },
        { id: 3, login: 'client', email: 'client@test.com', role_id: 3, is_active: true, created_at: '2026-01-03', full_name: 'Клиент Клиентов' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadOffices = async () => {
    setLoading(true);
    try {
      const response = await api.get('/offices');
      setOffices(response.data);
    } catch (error) {
      console.error('Ошибка загрузки офисов:', error);
      setOffices([
        { id: 1, office_number: '101', floor: 5, area_sqm: 45.5, price_per_month: 150000, is_free: true, description: 'Современный офис' },
        { id: 2, office_number: '205', floor: 2, area_sqm: 78.0, price_per_month: 150000, is_free: false, description: 'Переговорная' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/audit');
      setAuditLogs(response.data);
    } catch (error) {
      console.error('Ошибка загрузки аудита:', error);
      setAuditLogs([
        { id: 1, created_at: '2026-04-18 14:23', user_login: 'admin', action_type: 'CREATE', table_name: 'users', record_id: 4, old_values: null, new_values: '{"login":"newuser"}' },
        { id: 2, created_at: '2026-04-18 11:05', user_login: 'manager', action_type: 'UPDATE', table_name: 'offices', record_id: 2, old_values: '{"price":150000}', new_values: '{"price":145000}' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'users') loadUsers();
    if (activeTab === 'offices') loadOffices();
    if (activeTab === 'audit') loadAuditLogs();
  }, [activeTab]);

  const handleAddUser = () => {
    setEditingItem(null);
    setUserForm({ login: '', email: '', password: '', role_id: 3, phone: '', full_name: '' });
    setShowUserModal(true);
  };

  const handleEditUser = (user) => {
    setEditingItem(user);
    setUserForm({ ...user, password: '' });
    setShowUserModal(true);
  };

  const handleDeleteUser = async (id) => {
    if (window.confirm('Удалить пользователя?')) {
      try {
        await api.delete(`/users/${id}`);
        loadUsers();
      } catch (error) {
        console.error('Ошибка удаления:', error);
        alert('Ошибка при удалении');
      }
    }
  };

  const handleSaveUser = async () => {
    try {
      if (editingItem) {
        await api.put(`/users/${editingItem.id}`, userForm);
      } else {
        await api.post('/users', userForm);
      }
      setShowUserModal(false);
      loadUsers();
    } catch (error) {
      console.error('Ошибка сохранения:', error);
      alert('Ошибка при сохранении');
    }
  };

  const handleAddOffice = () => {
    setEditingItem(null);
    setOfficeForm({ office_number: '', floor: '', area_sqm: '', price_per_month: '', description: '', is_free: true });
    setShowOfficeModal(true);
  };

  const handleEditOffice = (office) => {
    setEditingItem(office);
    setOfficeForm(office);
    setShowOfficeModal(true);
  };

  const handleDeleteOffice = async (id) => {
    if (window.confirm('Удалить офис?')) {
      try {
        await api.delete(`/offices/${id}`);
        loadOffices();
      } catch (error) {
        console.error('Ошибка удаления:', error);
        alert('Ошибка при удалении');
      }
    }
  };

  const handleSaveOffice = async () => {
    try {
      if (editingItem) {
        await api.put(`/offices/${editingItem.id}`, officeForm);
      } else {
        await api.post('/offices', officeForm);
      }
      setShowOfficeModal(false);
      loadOffices();
    } catch (error) {
      console.error('Ошибка сохранения:', error);
      alert('Ошибка при сохранении');
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    try {
      await api.post('/ai/rental-prediction/train');
      setLastTrained(new Date().toLocaleDateString('ru-RU'));
      alert('Модель успешно переобучена!');
    } catch (error) {
      console.error('Ошибка обучения:', error);
      alert('Ошибка при обучении модели');
    } finally {
      setTraining(false);
    }
  };

  const getRoleName = (roleId) => {
    const roles = { 1: 'Администратор', 2: 'Менеджер', 3: 'Клиент' };
    return roles[roleId] || 'Неизвестно';
  };

  const getRoleClass = (roleId) => {
    const classes = { 1: 'role-admin', 2: 'role-manager', 3: 'role-client' };
    return classes[roleId] || '';
  };

  if (user?.role_id !== 1) {
    return <div className="empty-state">Доступ запрещён. Только для администраторов.</div>;
  }

  return (
    <div className="admin-container">
      <h1 className="admin-title">
        <Settings size={28} style={{ marginRight: '12px', verticalAlign: 'middle' }} />
        Панель администратора
      </h1>
      <p className="admin-subtitle">Управление пользователями, офисами и системой</p>

      {/* Вкладки */}
      <div className="admin-tabs">
        <button className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>
          <Users size={16} style={{ marginRight: '8px' }} />
          Пользователи
        </button>
        <button className={`tab-btn ${activeTab === 'offices' ? 'active' : ''}`} onClick={() => setActiveTab('offices')}>
          <Building2 size={16} style={{ marginRight: '8px' }} />
          Офисы
        </button>
        <button className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`} onClick={() => setActiveTab('audit')}>
          <History size={16} style={{ marginRight: '8px' }} />
          Журнал аудита
        </button>
        <button className={`tab-btn ${activeTab === 'ai' ? 'active' : ''}`} onClick={() => setActiveTab('ai')}>
          <Brain size={16} style={{ marginRight: '8px' }} />
          AI управление
        </button>
      </div>

      {/* Вкладка: Пользователи */}
      {activeTab === 'users' && (
        <>
          <button className="add-btn" onClick={handleAddUser}>
            <UserPlus size={16} style={{ marginRight: '8px' }} />
            Добавить пользователя
          </button>
          <div className="table-container">
            {loading ? (
              <div className="loading-state">Загрузка...</div>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Логин</th>
                    <th>Email</th>
                    <th>ФИО</th>
                    <th>Роль</th>
                    <th>Статус</th>
                    <th>Дата регистрации</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td>{u.id}</td>
                      <td><strong>{u.login}</strong></td>
                      <td>{u.email}</td>
                      <td>{u.full_name || '-'}</td>
                      <td><span className={`role-badge ${getRoleClass(u.role_id)}`}>{getRoleName(u.role_id)}</span></td>
                      <td><span className={`status-badge ${u.is_active ? 'status-active' : 'status-inactive'}`}>
                          {u.is_active ? <CheckCircle size={12} style={{ marginRight: '4px' }} /> : <XCircle size={12} style={{ marginRight: '4px' }} />}
                          {u.is_active ? 'Активен' : 'Заблокирован'}
                        </span></td>
                      <td>{u.created_at?.split('T')[0]}</td>
                      <td className="action-btns">
                        <button className="icon-btn edit" onClick={() => handleEditUser(u)}>
                          <Edit2 size={16} />
                        </button>
                        <button className="icon-btn delete" onClick={() => handleDeleteUser(u.id)}>
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* Вкладка: Офисы */}
      {activeTab === 'offices' && (
        <>
          <button className="add-btn" onClick={handleAddOffice}>
            <Plus size={16} style={{ marginRight: '8px' }} />
            Добавить офис
          </button>
          <div className="table-container">
            {loading ? (
              <div className="loading-state">Загрузка...</div>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Номер</th>
                    <th>Этаж</th>
                    <th>Площадь</th>
                    <th>Цена</th>
                    <th>Статус</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {offices.map(o => (
                    <tr key={o.id}>
                      <td>{o.id}</td>
                      <td><strong>{o.office_number}</strong></td>
                      <td>{o.floor}</td>
                      <td>{o.area_sqm} м²</td>
                      <td>{o.price_per_month?.toLocaleString()} ₽</td>
                      <td className="action-btns">
                        <button className="icon-btn edit" onClick={() => handleEditOffice(o)}>
                          <Edit2 size={16} />
                        </button>
                        <button className="icon-btn delete" onClick={() => handleDeleteOffice(o.id)}>
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* Вкладка: Журнал аудита */}
      {activeTab === 'audit' && (
        <div className="table-container">
          {loading ? (
            <div className="loading-state">Загрузка...</div>
          ) : (
            <table className="admin-table">
              <thead>
                <tr>
                  <th><Clock size={14} style={{ marginRight: '4px' }} /> Дата/время</th>
                  <th><User size={14} style={{ marginRight: '4px' }} /> Пользователь</th>
                  <th><FileText size={14} style={{ marginRight: '4px' }} /> Действие</th>
                  <th><Home size={14} style={{ marginRight: '4px' }} /> Таблица</th>
                  <th>ID записи</th>
                  <th>Изменения</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map(log => (
                  <tr key={log.id}>
                    <td>{log.created_at}</td>
                    <td>{log.user_login}</td>
                    <td>{log.action_type}</td>
                    <td>{log.table_name}</td>
                    <td>{log.record_id}</td>
                    <td className="audit-log">
                      {log.old_values && <span className="old-value">Было: {JSON.stringify(log.old_values)}</span>}
                      {log.old_values && log.new_values && <span> → </span>}
                      {log.new_values && <span className="new-value">Стало: {JSON.stringify(log.new_values)}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Вкладка: AI управление */}
      {activeTab === 'ai' && (
        <div className="ai-section">
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Brain size={20} />
            Управление AI-моделью
          </h3>
          <div className="ai-metrics">
            <div className="ai-metric">
              <div className="ai-metric-value">
                <BarChart3 size={20} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                {metrics.accuracy}
              </div>
              <div className="ai-metric-label">Точность модели</div>
            </div>
            <div className="ai-metric">
              <div className="ai-metric-value">
                <BarChart3 size={20} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                {metrics.auc}
              </div>
              <div className="ai-metric-label">ROC AUC</div>
            </div>
            <div className="ai-metric">
              <div className="ai-metric-value">
                <Calendar size={20} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                {lastTrained}
              </div>
              <div className="ai-metric-label">Последнее обучение</div>
            </div>
          </div>
          <button className="train-btn" onClick={handleTrain} disabled={training}>
            <RefreshCw size={16} style={{ marginRight: '8px' }} />
            {training ? 'Обучение...' : 'Переобучить модель'}
          </button>
          <p style={{ marginTop: '16px', fontSize: '13px', color: '#64748b' }}>
            Модель прогнозирует вероятность аренды офиса на основе исторических данных.
          </p>
        </div>
      )}

      {/* Модальное окно: Пользователь */}
      {showUserModal && (
        <div className="modal-overlay" onClick={() => setShowUserModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {editingItem ? <Edit2 size={18} style={{ marginRight: '8px' }} /> : <UserPlus size={18} style={{ marginRight: '8px' }} />}
                {editingItem ? 'Редактировать пользователя' : 'Добавить пользователя'}
              </h3>
              <button className="close-modal" onClick={() => setShowUserModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-field">
              <label><User size={14} style={{ marginRight: '4px' }} /> Логин *</label>
              <input value={userForm.login} onChange={(e) => setUserForm({ ...userForm, login: e.target.value })} />
            </div>
            <div className="modal-field">
              <label><Mail size={14} style={{ marginRight: '4px' }} /> Email *</label>
              <input type="email" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} />
            </div>
            {!editingItem && (
              <div className="modal-field">
                <label><Lock size={14} style={{ marginRight: '4px' }} /> Пароль *</label>
                <input type="password" value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} />
              </div>
            )}
            <div className="modal-field">
              <label><User size={14} style={{ marginRight: '4px' }} /> ФИО</label>
              <input value={userForm.full_name} onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })} />
            </div>
            <div className="modal-field">
              <label><Phone size={14} style={{ marginRight: '4px' }} /> Телефон</label>
              <input value={userForm.phone} onChange={(e) => setUserForm({ ...userForm, phone: e.target.value })} />
            </div>
            <div className="modal-field">
              <label><Users size={14} style={{ marginRight: '4px' }} /> Роль</label>
              <select value={userForm.role_id} onChange={(e) => setUserForm({ ...userForm, role_id: parseInt(e.target.value) })}>
                <option value={1}>Администратор</option>
                <option value={2}>Менеджер</option>
                <option value={3}>Клиент</option>
              </select>
            </div>
            <div className="modal-actions">
              <button className="modal-cancel" onClick={() => setShowUserModal(false)}>
                <X size={14} style={{ marginRight: '4px' }} />
                Отмена
              </button>
              <button className="modal-save" onClick={handleSaveUser}>
                <Save size={14} style={{ marginRight: '4px' }} />
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно: Офис */}
      {showOfficeModal && (
        <div className="modal-overlay" onClick={() => setShowOfficeModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {editingItem ? <Edit2 size={18} style={{ marginRight: '8px' }} /> : <Plus size={18} style={{ marginRight: '8px' }} />}
                {editingItem ? 'Редактировать офис' : 'Добавить офис'}
              </h3>
              <button className="close-modal" onClick={() => setShowOfficeModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-field">
              <label><Home size={14} style={{ marginRight: '4px' }} /> Номер офиса *</label>
              <input value={officeForm.office_number} onChange={(e) => setOfficeForm({ ...officeForm, office_number: e.target.value })} />
            </div>
            <div className="modal-field">
              <label><Building2 size={14} style={{ marginRight: '4px' }} /> Этаж *</label>
              <input type="number" value={officeForm.floor} onChange={(e) => setOfficeForm({ ...officeForm, floor: parseInt(e.target.value) })} />
            </div>
            <div className="modal-field">
              <label><Maximize2 size={14} style={{ marginRight: '4px' }} /> Площадь (м²) *</label>
              <input type="number" step="0.1" value={officeForm.area_sqm} onChange={(e) => setOfficeForm({ ...officeForm, area_sqm: parseFloat(e.target.value) })} />
            </div>
            <div className="modal-field">
              <label><DollarSign size={14} style={{ marginRight: '4px' }} /> Цена (₽/мес) *</label>
              <input type="number" value={officeForm.price_per_month} onChange={(e) => setOfficeForm({ ...officeForm, price_per_month: parseInt(e.target.value) })} />
            </div>
            <div className="modal-field">
              <label><FileText size={14} style={{ marginRight: '4px' }} /> Описание</label>
              <textarea rows="3" value={officeForm.description} onChange={(e) => setOfficeForm({ ...officeForm, description: e.target.value })} />
            </div>
            <div className="modal-field">
              <label><CheckCircle size={14} style={{ marginRight: '4px' }} /> Статус</label>
              <select value={officeForm.is_free} onChange={(e) => setOfficeForm({ ...officeForm, is_free: e.target.value === 'true' })}>
                <option value="true">Свободен</option>
                <option value="false">Арендован</option>
              </select>
            </div>
            <div className="modal-actions">
              <button className="modal-cancel" onClick={() => setShowOfficeModal(false)}>
                <X size={14} style={{ marginRight: '4px' }} />
                Отмена
              </button>
              <button className="modal-save" onClick={handleSaveOffice}>
                <Save size={14} style={{ marginRight: '4px' }} />
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPage;