import React, { useEffect, useState } from 'react';

const ForecastPage = () => {
  const [forecasts, setForecasts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: заменить на реальный API
    setTimeout(() => {
      setForecasts([
        { office_number: '101', probability: 85, category: 'high' },
        { office_number: '205', probability: 45, category: 'low' },
        { office_number: '312', probability: 92, category: 'high' },
        { office_number: '418', probability: 28, category: 'low' },
        { office_number: '524', probability: 76, category: 'medium' },
      ]);
      setLoading(false);
    }, 300);
  }, []);

  if (loading) return <div>Загрузка прогноза...</div>;

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '20px' }}>
      <h1>Прогноз заполняемости офисов</h1>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#f0f0f0' }}>
            <th style={{ padding: '10px', border: '1px solid #ddd' }}>Офис</th>
            <th style={{ padding: '10px', border: '1px solid #ddd' }}>Прогноз</th>
            <th style={{ padding: '10px', border: '1px solid #ddd' }}>Риск</th>
          </tr>
        </thead>
        <tbody>
          {forecasts.map(f => (
            <tr key={f.office_number}>
              <td style={{ padding: '10px', border: '1px solid #ddd' }}>{f.office_number}</td>
              <td style={{ padding: '10px', border: '1px solid #ddd' }}>{f.probability}%</td>
              <td style={{
                padding: '10px',
                border: '1px solid #ddd',
                color: f.category === 'high' ? 'green' : f.category === 'low' ? 'red' : 'orange'
              }}>
                {f.category === 'high' ? 'Низкий' : f.category === 'low' ? 'Высокий' : 'Средний'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ForecastPage;