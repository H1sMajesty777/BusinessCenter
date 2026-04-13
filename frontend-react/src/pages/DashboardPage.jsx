import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [offices, setOffices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Мок-данные офисов
  const mockOffices = [
    { id: 1, office_number: "101", floor: 5, area_sqm: 45.5, price_per_month: 150000, is_free: true },
    { id: 2, office_number: "205", floor: 2, area_sqm: 78.0, price_per_month: 150000, is_free: false },
    { id: 3, office_number: "312", floor: 3, area_sqm: 32.0, price_per_month: 150000, is_free: true },
    { id: 4, office_number: "418", floor: 4, area_sqm: 56.2, price_per_month: 150000, is_free: false },
    { id: 5, office_number: "524", floor: 5, area_sqm: 92.0, price_per_month: 150000, is_free: true },
    { id: 6, office_number: "102", floor: 1, area_sqm: 25.5, price_per_month: 150000, is_free: true },
  ];

  useEffect(() => {
    // Имитация загрузки
    setTimeout(() => {
      setOffices(mockOffices);
      setLoading(false);
    }, 500);
  }, []);

  if (loading) return <div>Загрузка офисов...</div>;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
      <h1>Найдите идеальный офис</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {offices.map(office => (
          <div key={office.id} style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px' }}>
            <h3>Офис {office.office_number}</h3>
            <p>Этаж: {office.floor}</p>
            <p>Площадь: {office.area_sqm} м²</p>
            <p>Цена: {office.price_per_month.toLocaleString()} ₽/мес</p>
            <button>Забронировать</button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DashboardPage;