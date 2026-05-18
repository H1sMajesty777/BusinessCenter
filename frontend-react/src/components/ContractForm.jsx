// frontend/src/components/ContractForm.jsx
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { X, Calendar, DollarSign, FileText, CheckCircle, AlertCircle } from 'lucide-react';

const ContractForm = ({ application, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    monthly_amount: 0,
    total_amount: 0,
    deposit_amount: 0,
    special_conditions: ''
  });
  
  // ========== ФУНКЦИЯ РАСЧЁТА МЕСЯЦЕВ ==========
  const calculateMonths = () => {
    if (!formData.start_date || !formData.end_date) return 0;
    const start = new Date(formData.start_date);
    const end = new Date(formData.end_date);
    const months = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth()) + 1;
    return months;
  };
  
  // ========== АВТОМАТИЧЕСКИЙ РАСЧЁТ ОБЩЕЙ СУММЫ ==========
  useEffect(() => {
    if (formData.monthly_amount && formData.start_date && formData.end_date) {
      const months = calculateMonths();
      setFormData(prev => ({
        ...prev,
        total_amount: prev.monthly_amount * months
      }));
    }
  }, [formData.monthly_amount, formData.start_date, formData.end_date]);
  
  // Устанавливаем рекомендуемую цену при загрузке
  useEffect(() => {
    if (application?.office_price) {
      setFormData(prev => ({
        ...prev,
        monthly_amount: application.office_price
      }));
    }
  }, [application]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const contractData = {
        application_id: application.id,
        user_id: application.user_id,
        office_id: application.office_id,
        start_date: formData.start_date,
        end_date: formData.end_date,
        total_amount: formData.total_amount,
        monthly_amount: formData.monthly_amount,
        deposit_amount: formData.deposit_amount,
        special_conditions: formData.special_conditions
      };
      
      const response = await api.post('/contracts', contractData);
      
      if (response.data) {
        setSuccess(true);
        setTimeout(() => {
          if (onSuccess) onSuccess(response.data);
          onClose();
        }, 2000);
      }
      
    } catch (error) {
      console.error('Ошибка создания договора:', error);
      alert(error.response?.data?.detail || 'Ошибка при создании договора');
    } finally {
      setLoading(false);
    }
  };
  
  const monthsCount = calculateMonths();
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content contract-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            <FileText size={20} />
            Создание договора аренды
          </h3>
          <button className="close-modal" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        {success ? (
          <div className="success-state">
            <CheckCircle size={64} color="#22c55e" />
            <h4>Договор успешно создан!</h4>
            <p>Статус заявки обновлён, офис помечен как арендованный</p>
            <p>Создано {monthsCount} платежей на общую сумму {formData.total_amount.toLocaleString()} ₽</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="contract-form-section">
              <h4>Информация об аренде</h4>
              
              <div className="contract-form-row">
                <div className="contract-form-group">
                  <label><Calendar size={14} /> Дата начала</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    required
                  />
                </div>
                
                <div className="contract-form-group">
                  <label><Calendar size={14} /> Дата окончания</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    required
                  />
                </div>
              </div>
              
              <div className="contract-form-row">
                <div className="contract-form-group">
                  <label><DollarSign size={14} /> Ежемесячный платёж (₽)</label>
                  <input
                    type="number"
                    value={formData.monthly_amount}
                    onChange={(e) => setFormData({ ...formData, monthly_amount: parseFloat(e.target.value) })}
                    placeholder="Сумма в месяц"
                    required
                  />
                  <small>Рекомендуемая сумма: {application?.office_price?.toLocaleString()} ₽/мес</small>
                </div>
                
                <div className="contract-form-group">
                  <label><DollarSign size={14} /> Общая сумма договора (₽)</label>
                  <input
                    type="number"
                    value={formData.total_amount}
                    disabled
                    style={{ background: '#f3f4f6' }}
                  />
                  <small>{formData.monthly_amount} ₽ × {monthsCount} мес = {formData.total_amount.toLocaleString()} ₽</small>
                </div>
              </div>
              
              <div className="contract-form-row">
                <div className="contract-form-group">
                  <label><DollarSign size={14} /> Депозит/Залог (₽)</label>
                  <input
                    type="number"
                    value={formData.deposit_amount}
                    onChange={(e) => setFormData({ ...formData, deposit_amount: parseFloat(e.target.value) })}
                    placeholder="Сумма залога"
                  />
                  <small>Обычно = 1 месяц аренды</small>
                </div>
              </div>
              
              <div className="contract-form-group">
                <label><FileText size={14} /> Особые условия</label>
                <textarea
                  rows="3"
                  value={formData.special_conditions}
                  onChange={(e) => setFormData({ ...formData, special_conditions: e.target.value })}
                  placeholder="Дополнительные условия договора..."
                />
              </div>
            </div>
            
            <div className="info-banner">
              <AlertCircle size={16} />
              <span>После создания договора:</span>
              <ul>
                <li>Статус заявки изменится на "Договор создан"</li>
                <li>Офис будет помечен как арендованный</li>
                <li>Будут автоматически созданы платежи на каждый месяц аренды</li>
              </ul>
            </div>
            
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={onClose}>
                Отмена
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Создание...' : 'Создать договор'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ContractForm;