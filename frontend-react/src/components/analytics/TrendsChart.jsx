// frontend/src/components/analytics/TrendsChart.jsx
import React, { useState } from 'react';
import { LineChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Calendar, TrendingUp, BarChart3 } from 'lucide-react';

const TrendsChart = ({ data }) => {
  const [chartType, setChartType] = useState('line');
  
  const chartData = data.views_trend?.map((item, idx) => ({
    date: item.date?.slice(5),
    просмотры: item.views,
    уникальные: item.unique_users,
    заявки: data.applications_trend?.[idx]?.applications || 0,
    договоры: data.contracts_trend?.[idx]?.contracts || 0
  })) || [];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <div className="tooltip-date">{label}</div>
          {payload.map((p, idx) => (
            <div key={idx} className="tooltip-item">
              <span className="tooltip-color" style={{ background: p.color }} />
              <span>{p.name}: </span>
              <strong>{p.value}</strong>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="trends-chart-container">
      <div className="chart-header">
        <div>
          <h3 className="chart-title">
            <TrendingUp size={18} />
            Тренды активности
          </h3>
          <p className="chart-subtitle">Динамика просмотров, заявок и договоров за последние 30 дней</p>
        </div>
        <div className="chart-controls">
          <button 
            className={`chart-type-btn ${chartType === 'line' ? 'active' : ''}`}
            onClick={() => setChartType('line')}
          >
            <BarChart3 size={14} />
            Линии
          </button>
          <button 
            className={`chart-type-btn ${chartType === 'area' ? 'active' : ''}`}
            onClick={() => setChartType('area')}
          >
            <TrendingUp size={14} />
            Области
          </button>
        </div>
      </div>
      
      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={320}>
          {chartType === 'line' ? (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="просмотры" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line 
                type="monotone" 
                dataKey="заявки" 
                stroke="#f59e0b" 
                strokeWidth={2}
                dot={{ fill: '#f59e0b', r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="договоры" 
                stroke="#10b981" 
                strokeWidth={2}
                dot={{ fill: '#10b981', r: 4 }}
              />
            </LineChart>
          ) : (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="просмотры" 
                stroke="#3b82f6" 
                fill="#3b82f6" 
                fillOpacity={0.1}
              />
              <Area 
                type="monotone" 
                dataKey="заявки" 
                stroke="#f59e0b" 
                fill="#f59e0b" 
                fillOpacity={0.1}
              />
              <Area 
                type="monotone" 
                dataKey="договоры" 
                stroke="#10b981" 
                fill="#10b981" 
                fillOpacity={0.1}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      ) : (
        <div className="chart-empty">Нет данных для отображения</div>
      )}
    </div>
  );
};

export default TrendsChart;