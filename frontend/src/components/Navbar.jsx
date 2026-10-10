import React from 'react';

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Executive Dashboard', icon: '📊' },
    { id: 'forecasts', label: 'Demand Forecasts', icon: '📈' },
    { id: 'stores', label: 'Store Fleet', icon: '🏬' },
    { id: 'analytics', label: 'ML Performance', icon: '⚡' },
  ];

  return (
    <aside className="sidebar">
      <div className="brand-section">
        <div className="brand-logo">RF</div>
        <div>
          <div className="brand-title">RetailForecast AI</div>
          <div className="brand-subtitle">Walmart Inventory System</div>
        </div>
      </div>

      <ul className="nav-links">
        {navItems.map((item) => (
          <li key={item.id}>
            <button
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
              style={{ width: '100%', textAlign: 'left', border: 'none', background: 'transparent' }}
            >
              <span style={{ fontSize: '16px' }}>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          </li>
        ))}
      </ul>

      {/* Real-time Infrastructure Cluster Status Box */}
      <div className="cluster-status-box">
        <div className="cluster-title">Big Data Infrastructure</div>
        <div className="status-badge-row">
          <div className="status-badge">
            <span><span className="status-dot active"></span>Kafka Streaming</span>
            <span style={{ color: '#10b981', fontSize: '11px', fontWeight: 600 }}>READY</span>
          </div>
          <div className="status-badge">
            <span><span className="status-dot active"></span>Hadoop HDFS</span>
            <span style={{ color: '#10b981', fontSize: '11px', fontWeight: 600 }}>ONLINE</span>
          </div>
          <div className="status-badge">
            <span><span className="status-dot active"></span>PySpark Engine</span>
            <span style={{ color: '#10b981', fontSize: '11px', fontWeight: 600 }}>ACTIVE</span>
          </div>
          <div className="status-badge">
            <span><span className="status-dot active"></span>PostgreSQL DB</span>
            <span style={{ color: '#10b981', fontSize: '11px', fontWeight: 600 }}>CONNECTED</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
