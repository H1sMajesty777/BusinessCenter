import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getOfficeById } from '../services/officesService';

const OfficeDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [office, setOffice] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadOffice = async () => {
      try {
        const data = await getOfficeById(id);
        setOffice(data);
      } catch (error) {
        console.error('Ошибка загрузки офиса:', error);
      } finally {
        setLoading(false);
      }
    };
    loadOffice();
  }, [id]);

  const handleBook = () => {
    alert(`Офис ${office.office_number} добавлен в бронирование`);
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '50px' }}>Загрузка...</div>;
  }

  if (!office) {
    return <div style={{ textAlign: 'center', padding: '50px' }}>Офис не найден</div>;
  }

  // Парсим amenities если есть
  const amenities = office.amenities ? JSON.parse(office.amenities) : {};

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '20px' }}>
      <button 
        onClick={() => navigate('/dashboard')}
        style={{
          background: 'none',
          border: 'none',
          color: '#2563eb',
          cursor: 'pointer',
          marginBottom: '20px',
          fontSize: '14px'
        }}
      >
        ← Назад к списку
      </button>
      
      <div style={{
        background: 'white',
        borderRadius: '24px',
        padding: '30px',
        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '15px' }}>
          <h1 style={{ fontSize: '32px', margin: 0 }}>Офис {office.office_number}</h1>
          <span style={{
            padding: '8px 20px',
            borderRadius: '30px',
            background: office.is_free ? '#dcfce7' : '#fee2e2',
            color: office.is_free ? '#166534' : '#991b1b',
            fontWeight: '600'
          }}>
            {office.is_free ? 'Свободен' : 'Занят'}
          </span>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginBottom: '30px' }}>
          <div>
            <div style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '16px',
              height: '250px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '80px',
              color: 'white'
            }}>
              🏢
            </div>
          </div>
          
          <div>
            <h3 style={{ marginBottom: '16px', color: '#1e293b' }}>Характеристики</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '12px' }}>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Этаж</div>
                <div style={{ fontSize: '20px', fontWeight: '600' }}>{office.floor}</div>
              </div>
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '12px' }}>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Площадь</div>
                <div style={{ fontSize: '20px', fontWeight: '600' }}>{office.area_sqm} м²</div>
              </div>
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '12px' }}>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Ставка</div>
                <div style={{ fontSize: '20px', fontWeight: '600' }}>{office.price_per_month.toLocaleString()} ₽/мес</div>
              </div>
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '12px' }}>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Цена за м²</div>
                <div style={{ fontSize: '20px', fontWeight: '600' }}>
                  {Math.round(office.price_per_month / office.area_sqm).toLocaleString()} ₽
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {office.description && (
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ marginBottom: '12px' }}>Описание</h3>
            <p style={{ color: '#475569', lineHeight: '1.6' }}>{office.description}</p>
          </div>
        )}
        
        {Object.keys(amenities).length > 0 && (
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ marginBottom: '12px' }}>Оснащение</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
              {Object.entries(amenities).map(([key, value]) => (
                value && (
                  <span key={key} style={{
                    background: '#f1f5f9',
                    padding: '6px 14px',
                    borderRadius: '20px',
                    fontSize: '13px',
                    color: '#334155'
                  }}>
                    {key === 'wifi' ? 'Wi-Fi' :
                     key === 'parking' ? 'Парковка' :
                     key === 'elevator' ? 'Лифт' :
                     key === 'conditioning' ? 'Кондиционер' :
                     key === 'view' ? 'Вид на город' :
                     key === 'premium' ? 'Премиум' : key}
                  </span>
                )
              ))}
            </div>
          </div>
        )}
        
        <button
          onClick={handleBook}
          style={{
            width: '100%',
            padding: '14px',
            background: '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            fontSize: '16px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.background = '#1d4ed8'}
          onMouseLeave={(e) => e.target.style.background = '#2563eb'}
        >
          Забронировать офис
        </button>
      </div>
    </div>
  );
};

export default OfficeDetailPage;