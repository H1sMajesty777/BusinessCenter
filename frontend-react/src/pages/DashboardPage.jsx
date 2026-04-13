import React, { useEffect, useState } from 'react';
import '../styles/dashboard.css';

const DashboardPage = () => {
  const [offices, setOffices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Временно моки, потом заменю на реальный API
  useEffect(() => {
    // TODO: заменить на fetch('http://localhost:8000/api/offices')
    setTimeout(() => {
      setOffices([
        { id: 1, office_number: "101", floor: 5, area_sqm: 45.5, price_per_month: 150000, is_free: true },
        { id: 2, office_number: "205", floor: 2, area_sqm: 78.0, price_per_month: 150000, is_free: false },
        { id: 3, office_number: "312", floor: 3, area_sqm: 32.0, price_per_month: 150000, is_free: true },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  if (loading) return <div className="loading">Загрузка офисов...</div>;

  return (
    <div className="container">
      <div className="page-header">
        <h1>Найдите идеальный офис</h1>
        <p>Более 50 офисов от 20 до 200 м² в центре города</p>
      </div>

      <div className="offices-grid">
        {offices.map(office => (
          <div key={office.id} className="office-card">
            <div className="office-image">
              <div className="image-placeholder">
                <i data-lucide="building-2" style={{ width: '48px', height: '48px' }}></i>
              </div>
            </div>
            <div className="office-content">
              <div className="office-header">
                <span className="office-number">Офис {office.office_number}</span>
                <span className="office-floor">{office.floor} этаж</span>
              </div>
              <div className="office-details">
                <div className="detail-item">
                  <div className="detail-label">Площадь</div>
                  <div className="detail-value">{office.area_sqm} <small>м²</small></div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">Ставка</div>
                  <div className="detail-value">{office.price_per_month.toLocaleString()} <small>₽/мес</small></div>
                </div>
              </div>
              <div className="card-actions">
                <button className="card-btn primary">Забронировать</button>
                <button className="card-btn secondary">Подробнее</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DashboardPage;