import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { 
  Building2, MapPin, Ruler, ArrowUp, DollarSign, 
  CheckCircle, XCircle, Wifi, Car, Shield, Wind,
  Coffee, Maximize2, Bath, DoorOpen, Calendar, Clock,
  TrendingUp, TrendingDown, Minus, AlertCircle,
  ArrowLeft, Heart, CalendarCheck, Phone, Mail
} from 'lucide-react';
import '../styles/officeDetail.css';

const OfficeDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [office, setOffice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState(null);
  const [showApplicationForm, setShowApplicationForm] = useState(false);
  const [applicationData, setApplicationData] = useState({
    desired_date: '',
    comment: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [officeData, forecastData] = await Promise.all([
          api.get(`/offices/${id}`),
          api.get(`/ai/rental-prediction/office/${id}`).catch(() => ({ data: null }))
        ]);
        setOffice(officeData.data);
        setForecast(forecastData.data);
      } catch (error) {
        console.error('Ошибка загрузки офиса:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  const handleBook = () => {
    if (user) {
      setShowApplicationForm(true);
    } else {
      navigate('/login');
    }
  };

  const handleSubmitApplication = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/applications', {
        office_id: office.id,
        desired_date: applicationData.desired_date,
        comment: applicationData.comment
      });
      alert('Заявка успешно отправлена!');
      setShowApplicationForm(false);
      setApplicationData({ desired_date: '', comment: '' });
    } catch (error) {
      console.error('Ошибка отправки заявки:', error);
      alert('Ошибка при отправке заявки');
    } finally {
      setSubmitting(false);
    }
  };

  const getAmenityIcon = (key) => {
    const icons = {
      wifi: <Wifi size={18} />,
      parking: <Car size={18} />,
      elevator: <ArrowUp size={18} />,
      conditioning: <Wind size={18} />,
      security: <Shield size={18} />,
      kitchen: <Coffee size={18} />,
      view: <Maximize2 size={18} />,
      premium: <Star size={18} />,
      meeting_room: <Users size={18} />,
      lounge: <Coffee size={18} />,
      terrace: <Maximize2 size={18} />
    };
    return icons[key] || <CheckCircle size={18} />;
  };

  const getAmenityName = (key) => {
    const names = {
      wifi: 'Wi-Fi',
      parking: 'Парковка',
      elevator: 'Лифт',
      conditioning: 'Кондиционер',
      security: 'Охрана',
      kitchen: 'Кухня',
      view: 'Панорамные окна',
      premium: 'Премиум',
      meeting_room: 'Переговорная',
      lounge: 'Зона отдыха',
      terrace: 'Терраса'
    };
    return names[key] || key;
  };

  const getForecastColor = (probability) => {
    if (probability >= 70) return 'green';
    if (probability >= 50) return 'yellow';
    return 'red';
  };

  const getForecastIcon = (probability) => {
    if (probability >= 70) return <TrendingUp size={20} />;
    if (probability >= 50) return <Minus size={20} />;
    return <TrendingDown size={20} />;
  };

  if (loading) {
    return <div className="loading-state">Загрузка...</div>;
  }

  if (!office) {
    return <div className="empty-state">Офис не найден</div>;
  }

  const amenities = office.amenities ? JSON.parse(office.amenities) : {};

  return (
    <div className="office-detail-container">
      <button className="back-btn" onClick={() => navigate(-1)}>
        <ArrowLeft size={18} style={{ marginRight: '8px' }} />
        Назад к списку
      </button>

      <div className="office-detail-grid">
        {/* Левая колонка — изображение и удобства */}
        <div className="office-detail-left">
          <div className="office-image-large">
            <Building2 size={80} color="white" opacity={0.8} />
          </div>

          {Object.keys(amenities).length > 0 && (
            <div className="amenities-section">
              <h3>Оснащение офиса</h3>
              <div className="amenities-grid">
                {Object.entries(amenities).map(([key, value]) => (
                  value && (
                    <div key={key} className="amenity-item">
                      {getAmenityIcon(key)}
                      <span>{getAmenityName(key)}</span>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Правая колонка — информация */}
        <div className="office-detail-right">
          <div className="office-header">
            <div>
              <h1 className="office-title">Офис {office.office_number}</h1>
              <div className="office-address">
                <MapPin size={16} style={{ marginRight: '6px' }} />
                Бизнес-центр, {office.floor} этаж
              </div>
            </div>
            <div className={`office-status ${office.is_free ? 'status-free' : 'status-occupied'}`}>
              {office.is_free ? (
                <><CheckCircle size={16} style={{ marginRight: '6px' }} /> Свободен</>
              ) : (
                <><XCircle size={16} style={{ marginRight: '6px' }} /> Арендован</>
              )}
            </div>
          </div>

          <div className="specs-grid">
            <div className="spec-card">
              <Ruler size={20} className="spec-icon" />
              <div className="spec-label">Площадь</div>
              <div className="spec-value">{office.area_sqm} м²</div>
            </div>
            <div className="spec-card">
              <ArrowUp size={20} className="spec-icon" />
              <div className="spec-label">Этаж</div>
              <div className="spec-value">{office.floor}</div>
            </div>
            <div className="spec-card">
              <DollarSign size={20} className="spec-icon" />
              <div className="spec-label">Цена</div>
              <div className="spec-value">{office.price_per_month?.toLocaleString()} ₽/мес</div>
            </div>
          </div>

          {office.description && (
            <div className="description-section">
              <h3>Описание</h3>
              <p>{office.description}</p>
            </div>
          )}

          {/* AI Прогноз */}
          {forecast && (
            <div className={`forecast-section forecast-${getForecastColor(forecast.probability)}`}>
              <div className="forecast-header">
                <div className="forecast-title">
                  <Brain size={20} style={{ marginRight: '8px' }} />
                  AI-прогноз спроса
                </div>
                <div className="forecast-badge">
                  {getForecastIcon(forecast.probability)}
                  <span>{forecast.probability}%</span>
                </div>
              </div>
              <div className="forecast-bar-container">
                <div 
                  className={`forecast-bar fill-${getForecastColor(forecast.probability)}`}
                  style={{ width: `${forecast.probability}%` }}
                />
              </div>
              <div className="forecast-factors">
                <div className="factors-title">Ключевые факторы:</div>
                <ul>
                  {forecast.factors?.map((factor, idx) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          <button className="book-btn" onClick={handleBook}>
            <CalendarCheck size={18} style={{ marginRight: '8px' }} />
            Оставить заявку
          </button>
        </div>
      </div>

      {/* Модальное окно заявки */}
      {showApplicationForm && (
        <div className="modal-overlay" onClick={() => setShowApplicationForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                <CalendarCheck size={20} style={{ marginRight: '8px' }} />
                Заявка на офис {office.office_number}
              </h3>
              <button className="close-modal" onClick={() => setShowApplicationForm(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmitApplication}>
              <div className="modal-field">
                <label><Calendar size={16} style={{ marginRight: '6px' }} /> Желаемая дата просмотра</label>
                <input
                  type="date"
                  value={applicationData.desired_date}
                  onChange={(e) => setApplicationData({ ...applicationData, desired_date: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                  required
                />
              </div>
              <div className="modal-field">
                <label><MessageSquare size={16} style={{ marginRight: '6px' }} /> Комментарий</label>
                <textarea
                  rows="4"
                  value={applicationData.comment}
                  onChange={(e) => setApplicationData({ ...applicationData, comment: e.target.value })}
                  placeholder="Дополнительная информация..."
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="modal-cancel" onClick={() => setShowApplicationForm(false)}>
                  Отмена
                </button>
                <button type="submit" className="modal-save" disabled={submitting}>
                  {submitting ? 'Отправка...' : 'Отправить заявку'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default OfficeDetailPage;