import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import '../styles/forecast.css';

const ForecastPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role_id === 1;
  const [training, setTraining] = useState(false);

  // ЖЁСТКИЕ МОК-ДАННЫЕ ДЛЯ ГРАФИКА
  const chartData = [
    { name: '101', вероятность: 85 },
    { name: '102', вероятность: 88 },
    { name: '201', вероятность: 78 },
    { name: '205', вероятность: 45 },
    { name: '301', вероятность: 82 },
    { name: '312', вероятность: 92 },
    { name: '401', вероятность: 75 },
    { name: '418', вероятность: 28 },
    { name: '501', вероятность: 68 },
    { name: '524', вероятность: 76 },
  ];

  // Функция для определения цвета в зависимости от процента
  const getBarColor = (probability) => {
    if (probability >= 70) return '#22c55e';  // Зелёный — высокий спрос
    if (probability >= 50) return '#eab308';  // Жёлтый — средний спрос
    return '#ef4444';                          // Красный — низкий спрос
  };

  // ЖЁСТКИЕ МОК-ДАННЫЕ ДЛЯ ТАБЛИЦЫ
  const forecasts = [
    { id: 1, office_number: '101', floor: 5, area_sqm: 45.5, price_per_month: 150000, probability: 85, category: 'high', factors: ['Высокий трафик', 'Много просмотров'] },
    { id: 2, office_number: '102', floor: 1, area_sqm: 25.5, price_per_month: 150000, probability: 88, category: 'high', factors: ['Отдельный вход', 'Популярный этаж'] },
    { id: 3, office_number: '201', floor: 2, area_sqm: 45.0, price_per_month: 22000, probability: 78, category: 'high', factors: ['Светлый офис', 'Хорошая цена'] },
    { id: 4, office_number: '205', floor: 2, area_sqm: 100.0, price_per_month: 45000, probability: 45, category: 'low', factors: ['Высокая цена', 'Мало просмотров'] },
    { id: 5, office_number: '301', floor: 3, area_sqm: 55.0, price_per_month: 32000, probability: 82, category: 'high', factors: ['Дизайнерский ремонт'] },
    { id: 6, office_number: '312', floor: 3, area_sqm: 32.0, price_per_month: 150000, probability: 92, category: 'high', factors: ['Дизайнерский ремонт', 'Быстрое одобрение'] },
    { id: 7, office_number: '401', floor: 4, area_sqm: 50.0, price_per_month: 30000, probability: 75, category: 'medium', factors: ['Панорамные окна'] },
    { id: 8, office_number: '418', floor: 4, area_sqm: 56.2, price_per_month: 150000, probability: 28, category: 'low', factors: ['Долго не сдаётся'] },
    { id: 9, office_number: '501', floor: 5, area_sqm: 200.0, price_per_month: 120000, probability: 68, category: 'medium', factors: ['Премиальный этаж'] },
    { id: 10, office_number: '524', floor: 5, area_sqm: 92.0, price_per_month: 150000, probability: 76, category: 'medium', factors: ['Хороший вид'] },
  ];

  const getProbabilityClass = (probability) => {
    if (probability >= 70) return 'high';
    if (probability >= 50) return 'medium';
    return 'low';
  };

  const getCategoryClass = (category) => {
    if (category === 'high') return 'category-high';
    if (category === 'medium') return 'category-medium';
    return 'category-low';
  };

  const getCategoryText = (category) => {
    if (category === 'high') return 'Высокий';
    if (category === 'medium') return 'Средний';
    return 'Низкий';
  };

  const handleTrain = () => {
    setTraining(true);
    setTimeout(() => {
      alert('Модель успешно переобучена!');
      setTraining(false);
    }, 1500);
  };

  return (
    <div className="forecast-container">
      <h1 className="forecast-title">📊 Аналитика аренды</h1>
      <p className="forecast-subtitle">AI-прогноз спроса на свободные офисы</p>

      {/* ГРАФИК С ЦВЕТНЫМИ СТОЛБЦАМИ */}
      <div className="chart-section">
        <h2 className="section-title">📊 Прогноз спроса по офисам</h2>
        <p className="section-subtitle">Вероятность аренды в процентах (зелёный — высокий, жёлтый — средний, красный — низкий)</p>
        
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" label={{ value: '', position: 'insideBottom', offset: -10 }} />
            <YAxis label={{ value: '', angle: -90, position: 'insideLeft' }} domain={[0, 100]} />
            <Tooltip formatter={(value) => [`${value}%`, 'Вероятность']} />

            <Bar dataKey="вероятность" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.вероятность)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Легенда цветов */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '30px', marginTop: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '20px', height: '20px', background: '#22c55e', borderRadius: '4px' }}></div>
            <span style={{ fontSize: '13px' }}>Высокий спрос (≥70%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '20px', height: '20px', background: '#eab308', borderRadius: '4px' }}></div>
            <span style={{ fontSize: '13px' }}>Средний спрос (50-69%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '20px', height: '20px', background: '#ef4444', borderRadius: '4px' }}></div>
            <span style={{ fontSize: '13px' }}>Низкий спрос (&lt;50%)</span>
          </div>
        </div>
      </div>

      {/* ТАБЛИЦА */}
      <div className="table-section">
        <h2 className="section-title">Детальный прогноз по офисам</h2>
        
        <table className="forecast-table">
          <thead>
            <tr>
              <th>Офис</th>
              <th>Этаж</th>
              <th>Площадь</th>
              <th>Цена</th>
              <th>Вероятность</th>
              <th>Категория</th>
              <th>Факторы</th>
            </tr>
          </thead>
          <tbody>
            {forecasts.map(office => (
              <tr key={office.id}>
                <td><strong>{office.office_number}</strong></td>
                <td>{office.floor} эт</td>
                <td>{office.area_sqm} м²</td>
                <td>{office.price_per_month.toLocaleString()} ₽</td>
                <td>
                  <div className="probability-container">
                    <div className="probability-bar">
                      <div 
                        className={`probability-fill ${getProbabilityClass(office.probability)}`}
                        style={{ width: `${office.probability}%` }}
                      />
                    </div>
                    <span className="probability-value">{office.probability}%</span>
                  </div>
                </td>
                <td>
                  <span className={`category-badge ${getCategoryClass(office.category)}`}>
                    {getCategoryText(office.category)}
                  </span>
                </td>
                <td>
                  <div className="factors-list">
                    {office.factors.map((factor, idx) => (
                      <span key={idx} className="factor-tag">{factor}</span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
};

export default ForecastPage;