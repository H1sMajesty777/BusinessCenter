import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useFavorites } from '../contexts/FavoritesContext';
import api from '../services/api';
import { 
  Heart, Building2, MapPin, Ruler, 
  DollarSign, Eye, Brain, Phone, Mail, 
  Loader2, CalendarCheck, X, CheckCircle,
  Wifi, Coffee, Car, Shield, Clock, Users,
  TrendingUp, TrendingDown, Minus, Zap, Sparkles,
  ArrowLeft, Share2, Copy, FileText, MessageCircle,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import '../styles/officeDetail.css';
import { getFeatureInfo } from '../utils/featureMapping';
import { Edit3 } from 'lucide-react';
import OfficeEditor from '../components/OfficeEditor';

const OfficeDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { favorites, toggleFavorite } = useFavorites();
  const [office, setOffice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState(null);
  const [showApplicationForm, setShowApplicationForm] = useState(false);
  const [applicationData, setApplicationData] = useState({
    desired_date: '',
    comment: '',
    phone: user?.phone || '',
    full_name: user?.full_name || ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [applicationSuccess, setApplicationSuccess] = useState(false);
  const [copied, setCopied] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const isFav = favorites?.some(f => f.office_id === parseInt(id) || f.id === parseInt(id)) || false;
  const isClient = user?.role_id === 3;
  const isManagerOrAdmin = user?.role_id === 1 || user?.role_id === 2;
  const [showEditor, setShowEditor] = useState(false);

  const images = office?.images || [];
  const hasImages = images.length > 0;
  const currentImage = hasImages ? images[currentImageIndex] : null;

  const nextImage = () => {
    if (images.length > 0) {
      setCurrentImageIndex((prev) => (prev + 1) % images.length);
    }
  };

  const prevImage = () => {
    if (images.length > 0) {
      setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [officeData, forecastData] = await Promise.all([
          api.get(`/offices/${id}`),
          isManagerOrAdmin ? api.get(`/ai/rental-prediction/office/${id}`).catch(() => ({ data: null })) : Promise.resolve({ data: null })
        ]);
        setOffice(officeData.data);
        setForecast(forecastData.data);
        setCurrentImageIndex(0);
        
        if (isClient) {
          await api.post(`/offices/${id}/track-view`).catch(e => console.log('Track view error:', e));
        }
      } catch (error) {
        console.error('Ошибка загрузки офиса:', error);
        if (error.response?.status === 404) navigate('/dashboard');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id, navigate, isManagerOrAdmin, isClient]);

  const handleSubmitApplication = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/applications', {
        office_id: office.id,
        desired_date: applicationData.desired_date,
        comment: applicationData.comment,
        phone: applicationData.phone,
        full_name: applicationData.full_name
      });
      setApplicationSuccess(true);
      setTimeout(() => {
        setShowApplicationForm(false);
        setApplicationSuccess(false);
        setApplicationData({ desired_date: '', comment: '', phone: user?.phone || '', full_name: user?.full_name || '' });
      }, 2000);
    } catch (error) {
      console.error('Ошибка отправки заявки:', error);
      alert(error.response?.data?.detail || 'Ошибка при отправке');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFavoriteClick = async () => {
    if (office) await toggleFavorite(office);
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatNumber = (num) => num?.toLocaleString() || 0;
  const probability = (forecast?.probability || 0) * 100;
  const probabilityPercent = Math.round(probability);

  const amenitiesList = [
    { icon: Wifi, label: 'Wi-Fi', available: true },
    { icon: Coffee, label: 'Кухня', available: true },
    { icon: Car, label: 'Парковка', available: true },
    { icon: Shield, label: 'Охрана', available: true },
    { icon: Clock, label: 'Круглосуточно', available: true },
    { icon: Users, label: 'Конференц-зал', available: office?.area_sqm > 50 }
  ];
  
  const handleEditOffice = () => {
    setShowEditor(true);
  };

  const handleOfficeSaved = (updatedOffice) => {
    setOffice(updatedOffice);
    setShowEditor(false);
  };

  if (loading) {
    return (
      <div className="detail-loading">
        <div className="loading-spinner">
          <Loader2 size={48} className="spin" />
        </div>
        <p>Загрузка информации об офисе...</p>
      </div>
    );
  }

  if (!office) {
    return (
      <div className="detail-error">
        <Building2 size={64} />
        <h3>Офис не найден</h3>
        <p>К сожалению, запрашиваемый офис не существует или был удален</p>
        <button onClick={() => navigate('/dashboard')}>Вернуться к списку</button>
      </div>
    );
  }

  return (
    <div className="office-detail-new">
      {/* Hero секция с изображением */}
      <div className="detail-hero">
        <div className="detail-hero-bg">
          <div className="hero-gradient"></div>
          <div className="hero-pattern"></div>
        </div>
        
        {/* Фоновое изображение офиса */}
        {hasImages && (
          <div className="hero-background-image">
            <img 
              src={`http://localhost:8000${images[0].image_url}`}
              alt={`Офис ${office.office_number}`}
            />
            <div className="hero-overlay"></div>
          </div>
        )}
        
        <div className="detail-hero-content">
          <button className="back-button" onClick={() => navigate('/dashboard')}>
            <ArrowLeft size={18} />
            Назад к офисам
          </button>
          
          <div className="hero-main">
            <div className="hero-info">
              <div className="office-badge">
                <span className="badge-number">Офис {office.office_number}</span>
                <span className={`status-badge ${office.is_free ? 'free' : 'rented'}`}>
                  {office.is_free ? 'Свободен' : 'Арендован'}
                </span>
              </div>
              
              <h1 className="office-title">
                {office.office_number}
                <span className="title-floor">на {office.floor} этаже</span>
              </h1>
              
              <div className="office-location">
                <MapPin size={16} />
                <span>Бизнес-центр «Премьер», помещение {office.room || office.office_number}</span>
              </div>
              
              <div className="hero-stats">
                <div className="hero-stat">
                  <Ruler size={18} />
                  <div>
                    <span className="stat-label">Площадь</span>
                    <span className="stat-value">{office.area_sqm} м²</span>
                  </div>
                </div>
                <div className="hero-stat">
                  <DollarSign size={18} />
                  <div>
                    <span className="stat-label">Стоимость</span>
                    <span className="stat-value">{formatNumber(office.price_per_month)} ₽/мес</span>
                  </div>
                </div>
                <div className="hero-stat">
                  <Eye size={18} />
                  <div>
                    <span className="stat-label">Просмотры</span>
                    <span className="stat-value">{office.views_30d || 0} в мес</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="hero-actions">
              <button className="action-btn favorite" onClick={handleFavoriteClick}>
                <Heart size={20} fill={isFav ? '#ef4444' : 'none'} color={isFav ? '#ef4444' : '#64748b'} />
                <span>{isFav ? 'В избранном' : 'В избранное'}</span>
              </button>
              <button className="action-btn share" onClick={handleCopyLink}>
                {copied ? <CheckCircle size={20} /> : <Share2 size={20} />}
                <span>{copied ? 'Скопировано!' : 'Поделиться'}</span>
              </button>
              {isManagerOrAdmin && (
                <button className="action-btn edit" onClick={handleEditOffice}>
                  <Edit3 size={18} />
                  <span>Редактировать</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Остальной контент без изменений... */}
      <div className="detail-content">
        <div className="content-grid">
          <div className="content-left">
            {/* Секция изображений с каруселью */}
            <div className="image-section">
              <div className="main-image">
                {hasImages ? (
                  <>
                    <img 
                      src={`http://localhost:8000${currentImage.image_url}`}
                      alt={`Офис ${office.office_number}`}
                      className="detail-main-img"
                    />
                    {images.length > 1 && (
                      <>
                        <button className="detail-slider-prev" onClick={prevImage}>
                          <ChevronLeft size={24} />
                        </button>
                        <button className="detail-slider-next" onClick={nextImage}>
                          <ChevronRight size={24} />
                        </button>
                        <div className="detail-slider-dots">
                          {images.map((_, idx) => (
                            <span 
                              key={idx} 
                              className={`detail-dot ${idx === currentImageIndex ? 'active' : ''}`}
                              onClick={() => setCurrentImageIndex(idx)}
                            />
                          ))}
                        </div>
                      </>
                    )}
                  </>
                ) : (
                  <div className="image-placeholder gradient-1">
                    <Building2 size={80} />
                    <span>Офис {office.office_number}</span>
                  </div>
                )}
              </div>
              
              {hasImages && images.length > 1 && (
                <div className="image-thumbnails">
                  {images.map((img, idx) => (
                    <div 
                      key={img.id} 
                      className={`thumbnail ${idx === currentImageIndex ? 'active' : ''}`}
                      onClick={() => setCurrentImageIndex(idx)}
                    >
                      <img src={`http://localhost:8000${img.image_url}`} alt={`Фото ${idx + 1}`} />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="description-section">
              <h3>Описание помещения</h3>
              <p>
                {office.description || `Светлый и просторный офис площадью ${office.area_sqm} м² на ${office.floor} этаже 
                бизнес-центра «Премьер». Помещение имеет отдельный вход, современную отделку и полностью готово 
                к размещению сотрудников. Отличная транспортная доступность, развитая инфраструктура вокруг.`}
              </p>
            </div>

            <div className="amenities-section">
              <h3>Удобства и инфраструктура</h3>
              <div className="amenities-grid">
                {amenitiesList.map((item, idx) => {
                  const Icon = item.icon;
                  return (
                    <div key={idx} className={`amenity-item ${item.available ? 'available' : 'unavailable'}`}>
                      <Icon size={20} />
                      <span>{item.label}</span>
                      {item.available && <CheckCircle size={14} className="check-icon" />}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="content-right">
            {/* Заявка */}
            <div className="request-card">
              <div className="request-header">
                <Zap size={24} className="request-icon" />
                <h3>Заинтересованы?</h3>
                <p>Оставьте заявку, и мы свяжемся с вами</p>
              </div>
              
              {office.is_free ? (
                <button className="request-button" onClick={() => setShowApplicationForm(true)}>
                  <CalendarCheck size={18} />
                  Оставить заявку на просмотр
                </button>
              ) : (
                <div className="rented-message">
                  <Building2 size={24} />
                  <p>Этот офис уже арендован</p>
                  <span>Но вы можете посмотреть другие офисы</span>
                </div>
              )}
              
              <div className="contact-info">
                <div className="contact-line">
                  <Phone size={14} />
                  <a href="tel:+74951234567">+7 (495) 123-45-67</a>
                </div>
                <div className="contact-line">
                  <Mail size={14} />
                  <a href="mailto:rent@business-center.ru">rent@business-center.ru</a>
                </div>
              </div>
            </div>

            {/* AI Аналитика */}
            {isManagerOrAdmin && forecast && (
              <div className="ai-card">
                <div className="ai-header">
                  <Sparkles size={18} />
                  <span>AI-аналитика</span>
                </div>
                
                <div className="ai-probability">
                  <svg viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="52" fill="none" stroke="#e2e8f0" strokeWidth="8"/>
                    <circle 
                      cx="60" cy="60" r="52" fill="none" 
                      stroke={probabilityPercent >= 70 ? '#22c55e' : probabilityPercent >= 40 ? '#eab308' : '#ef4444'} 
                      strokeWidth="8"
                      strokeDasharray={`${2 * Math.PI * 52 * probabilityPercent / 100} ${2 * Math.PI * 52}`}
                      strokeLinecap="round"
                      transform="rotate(-90 60 60)"
                    />
                    <text x="60" y="50" textAnchor="middle" dominantBaseline="middle" fontSize="24" fontWeight="800">
                      {probabilityPercent}%
                    </text>
                    <text x="60" y="72" textAnchor="middle" dominantBaseline="middle" fontSize="10" fill="#64748b">
                      вероятность
                    </text>
                  </svg>
                </div>
                
                <div className={`ai-verdict ${probabilityPercent >= 70 ? 'high' : probabilityPercent >= 40 ? 'medium' : 'low'}`}>
                  {probabilityPercent >= 70 ? '🔥 Высокий спрос' :
                   probabilityPercent >= 40 ? '📈 Средний спрос' : '⚠️ Низкий спрос'}
                </div>
                
                <div className="ai-description">
                  {forecast?.description || (
                    probabilityPercent >= 70 ? 'Офис пользуется высоким спросом. Рекомендуется ускорить сделку.' :
                    probabilityPercent >= 40 ? 'Средний уровень интереса. Есть потенциал.' :
                    'Низкая активность. Рассмотрите корректировку цены.'
                  )}
                </div>

                {forecast?.top_factors?.length > 0 && (
                  <div className="ai-factors">
                    <h4>Ключевые факторы прогноза</h4>
                    {forecast.top_factors.slice(0, 4).map((factor, idx) => {
                      const info = getFeatureInfo(factor.feature);
                      const importancePercent = Math.min(100, Math.round(factor.importance * 100));
                      return (
                        <div key={idx} className="ai-factor">
                          <div className="factor-info">
                            <span className="factor-name">{info.name || factor.feature}</span>
                            <span className="factor-percent">{importancePercent}%</span>
                          </div>
                          <div className="factor-bar">
                            <div className="factor-fill" style={{ width: `${importancePercent}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {showApplicationForm && (
        <div className="detail-modal" onClick={() => setShowApplicationForm(false)}>
          <div className="detail-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="detail-modal-header">
              <h3>Заявка на офис {office.office_number}</h3>
              <button onClick={() => setShowApplicationForm(false)}>
                <X size={20} />
              </button>
            </div>
            
            {applicationSuccess ? (
              <div className="application-success">
                <CheckCircle size={64} color="#22c55e" />
                <h4>Заявка успешно отправлена!</h4>
                <p>Наш менеджер свяжется с вами в ближайшее время</p>
              </div>
            ) : (
              <form onSubmit={handleSubmitApplication}>
                <div className="detail-modal-field">
                  <label>Ваше имя *</label>
                  <input
                    type="text"
                    value={applicationData.full_name}
                    onChange={(e) => setApplicationData({ ...applicationData, full_name: e.target.value })}
                    placeholder="Иванов Иван Иванович"
                    required
                  />
                </div>
                
                <div className="detail-modal-field">
                  <label>Телефон *</label>
                  <input
                    type="tel"
                    value={applicationData.phone}
                    onChange={(e) => setApplicationData({ ...applicationData, phone: e.target.value })}
                    placeholder="+7 (___) ___-__-__"
                    required
                  />
                </div>
                
                <div className="detail-modal-field">
                  <label>Желаемая дата просмотра</label>
                  <input
                    type="date"
                    value={applicationData.desired_date}
                    onChange={(e) => setApplicationData({ ...applicationData, desired_date: e.target.value })}
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
                
                <div className="detail-modal-field">
                  <label>Комментарий</label>
                  <textarea
                    rows="3"
                    value={applicationData.comment}
                    onChange={(e) => setApplicationData({ ...applicationData, comment: e.target.value })}
                    placeholder="Удобное время для звонка, дополнительные вопросы..."
                  />
                </div>
                
                <div className="detail-modal-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowApplicationForm(false)}>
                    Отмена
                  </button>
                  <button type="submit" className="btn-primary" disabled={submitting}>
                    {submitting ? 'Отправка...' : 'Отправить заявку'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
      
      {showEditor && (
        <OfficeEditor
          office={office}
          onClose={() => setShowEditor(false)}
          onSave={handleOfficeSaved}
        />
      )}
    </div>
  );
};

export default OfficeDetailPage;