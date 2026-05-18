// frontend/src/components/OfficeEditor.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import {
  X, Building2, MapPin, Ruler, DollarSign, FileText,
  Image as ImageIcon, Upload, Trash2, Star, Save,
  CheckCircle, AlertCircle, RefreshCw,
  Wifi, Coffee, Car, Zap, Move, Users, Sparkles, Eye,
  Home
} from 'lucide-react';
import '../styles/officeEditor.css';

const OfficeEditor = ({ office, onClose, onSave }) => {
  const { user } = useAuth();
  const isManagerOrAdmin = user?.role_id === 1 || user?.role_id === 2;
  
  const [formData, setFormData] = useState({
    office_number: '',
    floor: '',
    room: '',
    area_sqm: '',
    price_per_month: '',
    description: '',
    is_free: true,
    amenities: {
      wifi: true,
      parking: false,
      kitchen: false,
      conditioning: false,
      elevator: false,
      meeting_room: false,
      premium: false,
      view: false
    }
  });
  
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('info');
  const [errors, setErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState('');
  const [dragActive, setDragActive] = useState(false);
  
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (office) {
      setFormData({
        office_number: office.office_number || '',
        floor: office.floor || '',
        room: office.room || '',
        area_sqm: office.area_sqm || '',
        price_per_month: office.price_per_month || '',
        description: office.description || '',
        is_free: office.is_free ?? true,
        amenities: {
          ...formData.amenities,
          ...(office.amenities || {})
        }
      });
      
      if (office.id) {
        loadImages();
      }
    }
  }, [office]);

  const loadImages = async () => {
    if (!office?.id) return;
    try {
      console.log('Загружаем изображения для офиса:', office.id);
      const response = await api.get(`/office-images/office/${office.id}`);
      console.log('Загружено изображений:', response.data.length);
      setImages(response.data || []);
    } catch (error) {
      console.error('Ошибка загрузки изображений:', error);
      setImages([]);
    }
  };

  const handleUpload = async (files) => {
    if (!files || files.length === 0) return;
    
    setUploading(true);
    
    for (const file of files) {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('is_primary', images.length === 0 ? 'true' : 'false');
      
      try {
        const response = await api.post(`/office-images/upload/${office.id}`, fd, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        setImages(prev => [...prev, response.data]);
      } catch (error) {
        console.error('Ошибка загрузки:', error);
      }
    }
    
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSetPrimary = async (imageId) => {
    try {
      await api.put(`/office-images/${imageId}`, { is_primary: true });
      setImages(prev => prev.map(img => ({
        ...img,
        is_primary: img.id === imageId
      })));
    } catch (error) {
      console.error('Ошибка:', error);
    }
  };

  const handleDeleteImage = async (imageId) => {
    if (!confirm('Удалить изображение?')) return;
    
    try {
      await api.delete(`/office-images/${imageId}`);
      setImages(prev => prev.filter(img => img.id !== imageId));
    } catch (error) {
      console.error('Ошибка удаления:', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setErrors({});
    setSuccessMessage('');
    
    try {
      const submitData = {
        office_number: formData.office_number,
        floor: parseInt(formData.floor),
        area_sqm: parseFloat(formData.area_sqm),
        price_per_month: parseFloat(formData.price_per_month),
        description: formData.description,
        amenities: formData.amenities,
        is_free: formData.is_free
      };
      
      if (formData.room) submitData.room = formData.room;
      
      let savedOffice;
      if (office?.id) {
        const response = await api.put(`/offices/${office.id}`, submitData);
        savedOffice = response.data;
        setSuccessMessage('Офис успешно обновлён!');
      } else {
        const response = await api.post('/offices', submitData);
        savedOffice = response.data;
        setSuccessMessage('Офис успешно создан!');
      }
      
      setTimeout(() => {
        onSave(savedOffice);
        onClose();
      }, 1500);
      
    } catch (error) {
      console.error('Ошибка:', error);
      if (error.response?.data?.detail) {
        setErrors({ general: error.response.data.detail });
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(f => f.type.startsWith('image/'));
    if (imageFiles.length > 0) {
      handleUpload(imageFiles);
    }
  }, []);

  const AmenityIcon = ({ name, icon: Icon, label }) => (
    <label className={`amenity-toggle ${formData.amenities[name] ? 'active' : ''}`}>
      <input
        type="checkbox"
        checked={formData.amenities[name] || false}
        onChange={(e) => setFormData(prev => ({
          ...prev,
          amenities: { ...prev.amenities, [name]: e.target.checked }
        }))}
      />
      <Icon size={18} />
      <span>{label}</span>
      {formData.amenities[name] && <CheckCircle size={14} className="check-icon" />}
    </label>
  );

  const amenitiesList = [
    { name: 'wifi', icon: Wifi, label: 'Wi-Fi' },
    { name: 'parking', icon: Car, label: 'Парковка' },
    { name: 'kitchen', icon: Coffee, label: 'Кухня' },
    { name: 'conditioning', icon: Zap, label: 'Кондиционер' },
    { name: 'elevator', icon: Move, label: 'Лифт' },
    { name: 'meeting_room', icon: Users, label: 'Переговорная' },
    { name: 'premium', icon: Sparkles, label: 'Премиум' },
    { name: 'view', icon: Eye, label: 'Вид из окна' }
  ];

  if (!isManagerOrAdmin) {
    return (
      <div className="office-editor-overlay" onClick={onClose}>
        <div className="office-editor-modal" onClick={(e) => e.stopPropagation()}>
          <div className="editor-header">
            <h2>Доступ запрещён</h2>
            <button className="close-btn" onClick={onClose}><X size={20} /></button>
          </div>
          <div className="editor-content">
            <p>Только менеджеры и администраторы могут редактировать офисы</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="office-editor-overlay" onClick={onClose}>
      <div className="office-editor-modal" onClick={(e) => e.stopPropagation()}>
        <div className="editor-header">
          <div className="editor-title">
            <Building2 size={24} />
            <h2>{office?.id ? 'Редактирование офиса' : 'Новый офис'}</h2>
            {office?.office_number && <span className="office-badge">Офис {office.office_number}</span>}
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        <div className="editor-tabs">
          <button className={`tab-btn ${activeTab === 'info' ? 'active' : ''}`} onClick={() => setActiveTab('info')}>
            <FileText size={16} />
            Основное
          </button>
          <button className={`tab-btn ${activeTab === 'images' ? 'active' : ''}`} onClick={() => setActiveTab('images')}>
            <ImageIcon size={16} />
            Изображения
            {images.length > 0 && <span className="tab-badge">{images.length}</span>}
          </button>
          <button className={`tab-btn ${activeTab === 'amenities' ? 'active' : ''}`} onClick={() => setActiveTab('amenities')}>
            <Home size={16} />
            Удобства
          </button>
        </div>
        
        <div className="editor-content">
          {successMessage && (
            <div className="success-banner">
              <CheckCircle size={18} />
              {successMessage}
            </div>
          )}
          
          {errors.general && (
            <div className="error-banner">
              <AlertCircle size={18} />
              {errors.general}
            </div>
          )}
          
          {activeTab === 'info' && (
            <div className="info-tab">
              <div className="form-grid">
                <div className="form-group">
                  <label><MapPin size={14} /> Номер офиса *</label>
                  <input
                    type="text"
                    value={formData.office_number}
                    onChange={(e) => setFormData({ ...formData, office_number: e.target.value })}
                    placeholder="Например: 101"
                  />
                </div>
                
                <div className="form-group">
                  <label><Building2 size={14} /> Этаж *</label>
                  <input
                    type="number"
                    value={formData.floor}
                    onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
                    placeholder="Этаж"
                  />
                </div>
                
                <div className="form-group">
                  <label><MapPin size={14} /> Помещение</label>
                  <input
                    type="text"
                    value={formData.room}
                    onChange={(e) => setFormData({ ...formData, room: e.target.value })}
                    placeholder="Номер помещения"
                  />
                </div>
                
                <div className="form-group">
                  <label><Ruler size={14} /> Площадь (м²) *</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.area_sqm}
                    onChange={(e) => setFormData({ ...formData, area_sqm: e.target.value })}
                    placeholder="Площадь"
                  />
                </div>
                
                <div className="form-group">
                  <label><DollarSign size={14} /> Цена (₽/мес) *</label>
                  <input
                    type="number"
                    value={formData.price_per_month}
                    onChange={(e) => setFormData({ ...formData, price_per_month: e.target.value })}
                    placeholder="Цена"
                  />
                </div>
                
                <div className="form-group full-width">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_free}
                      onChange={(e) => setFormData({ ...formData, is_free: e.target.checked })}
                    />
                    <span>Офис свободен для аренды</span>
                  </label>
                </div>
                
                <div className="form-group full-width">
                  <label><FileText size={14} /> Описание</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows="5"
                    placeholder="Подробное описание офиса, особенности, преимущества..."
                  />
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'images' && (
            <div className="images-tab">
              <div 
                className={`upload-area ${dragActive ? 'drag-active' : ''}`}
                onClick={() => fileInputRef.current?.click()}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={(e) => handleUpload(Array.from(e.target.files))}
                  style={{ display: 'none' }}
                />
                <div className="upload-icon">
                  <Upload size={32} />
                </div>
                <p>Нажмите или перетащите изображения</p>
                <span>PNG, JPG, JPEG, WEBP до 10MB</span>
                {uploading && <RefreshCw size={20} className="spin" />}
              </div>
              
              {images.length > 0 && (
                <div className="images-grid">
                  {images.map((img, idx) => (
                    <div key={img.id} className="image-card">
                      <div className="image-preview">
                        <img 
                        src={`${img.image_url}?t=${Date.now()}&id=${img.id}`}
                        alt={`Фото ${idx + 1}`}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        onError={(e) => {
                            console.error('Ошибка загрузки:', img.image_url);
                            // Пробуем с прямым URL
                            e.target.src = `http://localhost:8000${img.image_url}?t=${Date.now()}`;
                        }}
                        onLoad={() => console.log('✅ Загружено:', img.image_url)}
                        />
                        {img.is_primary && (
                          <div className="primary-badge">
                            <Star size={12} fill="#fbbf24" />
                            Основное
                          </div>
                        )}
                        <div className="image-overlay">
                          <button onClick={() => handleDeleteImage(img.id)} className="delete-btn">
                            <Trash2 size={16} />
                          </button>
                          {!img.is_primary && (
                            <button onClick={() => handleSetPrimary(img.id)} className="primary-btn">
                              <Star size={16} />
                            </button>
                          )}
                        </div>
                      </div>
                      <div className="image-info">
                        <span className="image-name">{img.file_name?.slice(0, 30)}</span>
                        <span className="image-size">{(img.file_size / 1024).toFixed(0)} KB</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {images.length === 0 && !uploading && (
                <div className="no-images">
                  <ImageIcon size={48} />
                  <p>Нет загруженных изображений</p>
                  <span>Загрузите хотя бы одно изображение для офиса</span>
                </div>
              )}
            </div>
          )}
          
          {activeTab === 'amenities' && (
            <div className="amenities-tab">
              <div className="amenities-grid">
                {amenitiesList.map(amenity => (
                  <AmenityIcon key={amenity.name} {...amenity} />
                ))}
              </div>
              <div className="amenities-preview">
                <h4>Предпросмотр удобств:</h4>
                <div className="preview-badges">
                  {Object.entries(formData.amenities).filter(([_, v]) => v).map(([key]) => (
                    <span key={key} className="preview-badge">
                      {amenitiesList.find(a => a.name === key)?.label || key}
                    </span>
                  ))}
                  {Object.entries(formData.amenities).filter(([_, v]) => !v).length === Object.keys(formData.amenities).length && (
                    <span className="preview-badge empty">Не выбрано</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="editor-footer">
          <button className="cancel-btn" onClick={onClose}>
            Отмена
          </button>
          <button className="save-btn" onClick={handleSave} disabled={saving}>
            {saving ? <RefreshCw size={16} className="spin" /> : <Save size={16} />}
            {saving ? 'Сохранение...' : 'Сохранить изменения'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OfficeEditor;