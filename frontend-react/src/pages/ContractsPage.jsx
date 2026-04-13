import React, { useEffect, useState } from 'react';

const ContractsPage = () => {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: заменить на реальный API
    setTimeout(() => {
      setContracts([
        { id: 1, office_number: '101', start_date: '2024-01-01', end_date: '2024-12-31', total_amount: 1800000 },
        { id: 2, office_number: '205', start_date: '2024-02-01', end_date: '2024-07-31', total_amount: 900000 },
      ]);
      setLoading(false);
    }, 300);
  }, []);

  if (loading) return <div>Загрузка договоров...</div>;

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '20px' }}>
      <h1>Мои договоры</h1>
      {contracts.length === 0 ? (
        <p>У вас пока нет договоров</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f0f0f0' }}>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Офис</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Начало</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Окончание</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Сумма</th>
            </tr>
          </thead>
          <tbody>
            {contracts.map(c => (
              <tr key={c.id}>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>{c.office_number}</td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>{c.start_date}</td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>{c.end_date}</td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>{c.total_amount.toLocaleString()} ₽</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ContractsPage;