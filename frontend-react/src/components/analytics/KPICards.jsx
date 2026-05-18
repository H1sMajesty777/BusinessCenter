// frontend/src/components/analytics/KPICards.jsx
import React from 'react';
import { TrendingUp, TrendingDown, Minus, Zap, Target, Building2, DollarSign } from 'lucide-react';

const KPICards = ({ stats, offices }) => {
  // stats приходит из API с полями: avg_probability, high_count, medium_count, low_count, potential_monthly_income
  const highCount = stats?.high_count || 0;
  const mediumCount = stats?.medium_count || 0;
  const lowCount = stats?.low_count || 0;
  const totalOffices = offices.length;

  const avgProbability = stats?.avg_probability 
    ? Math.round(stats.avg_probability * 100) 
    : 0;
    

const potentialIncome = stats?.potential_monthly_income || 0;
  
  const cards = [
    {
      title: 'Средняя вероятность',
      value: `${avgProbability}%`,
      icon: Target,
      trend: avgProbability > 50 ? 'up' : avgProbability > 30 ? 'stable' : 'down',
      color: avgProbability >= 70 ? '#10b981' : avgProbability >= 40 ? '#f59e0b' : '#3b82f6'
    },
    {
      title: 'Высокий спрос',
      value: highCount,
      subtitle: totalOffices ? `${Math.round(highCount / totalOffices * 100)}% от всех` : '0%',
      icon: Zap,
      trend: 'up',
      color: '#10b981'
    },
    {
      title: 'Потенциальный доход',
      value: potentialIncome ? `${(potentialIncome / 1000).toFixed(0)}K ₽` : '0 ₽',
      subtitle: 'при сдаче офисов с высоким спросом',
      icon: DollarSign,
      trend: 'stable',
      color: '#f59e0b'
    },
    {
      title: 'Требуют внимания',
      value: lowCount,
      subtitle: totalOffices ? `${Math.round(lowCount / totalOffices * 100)}% нуждаются в оптимизации` : '0%',
      icon: Building2,
      trend: 'down',
      color: '#ef4444'
    }
  ];

  const TrendIcon = ({ trend }) => {
    if (trend === 'up') return <TrendingUp size={20} className="trend-up" />;
    if (trend === 'down') return <TrendingDown size={20} className="trend-down" />;
    return <Minus size={20} className="trend-stable" />;
  };

  return (
    <div className="kpi-grid">
      {cards.map((card, idx) => (
        <div key={idx} className="kpi-card" style={{ borderTop: `3px solid ${card.color}` }}>
          <div className="kpi-header">
            <card.icon size={24} style={{ color: card.color }} />
            <TrendIcon trend={card.trend} />
          </div>
          <div className="kpi-value">{card.value}</div>
          <div className="kpi-title">{card.title}</div>
          {card.subtitle && <div className="kpi-subtitle">{card.subtitle}</div>}
        </div>
      ))}
    </div>
  );
};

export default KPICards;