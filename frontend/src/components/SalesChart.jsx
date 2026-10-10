import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts';

export default function SalesChart({ data, title = "Historical Weekly Sales Trend" }) {
  if (!data || data.length === 0) {
    return (
      <div className="glass-card">
        <div className="chart-title">{title}</div>
        <div className="loading-container">No historical sales data available.</div>
      </div>
    );
  }

  // Format currency in tooltips
  const formatTooltipValue = (value) => [`$${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 'Sales'];

  return (
    <div className="glass-card">
      <div className="chart-header">
        <div>
          <div className="chart-title">{title}</div>
          <div className="chart-subtitle">Aggregated retail sales series from HDFS Parquet</div>
        </div>
      </div>
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <AreaChart data={data} margin={{ top: 10, right: 20, left: 20, bottom: 0 }}>
            <defs>
              <linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="date" stroke="#6b7280" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#6b7280"
              fontSize={11}
              tickLine={false}
              tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
            />
            <Tooltip
              formatter={formatTooltipValue}
              contentStyle={{
                backgroundColor: '#111827',
                borderColor: 'rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#f9fafb'
              }}
            />
            <Area
              type="monotone"
              dataKey="sales"
              stroke="#3b82f6"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#salesGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
