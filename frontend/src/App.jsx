import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Forecasts from './pages/Forecasts';
import Stores from './pages/Stores';
import Analytics from './pages/Analytics';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'forecasts':
        return <Forecasts />;
      case 'stores':
        return <Stores />;
      case 'analytics':
        return <Analytics />;
      default:
        return <Dashboard />;
    }
  };

  const getPageHeaderTitle = () => {
    switch (activeTab) {
      case 'dashboard':
        return 'Executive Dashboard';
      case 'forecasts':
        return 'Demand Forecasting & Inventory Planning';
      case 'stores':
        return 'Retail Store Fleet Overview';
      case 'analytics':
        return 'Machine Learning Analytics & Validation';
      default:
        return 'Retail Forecasting System';
    }
  };

  return (
    <div className="app-container">
      {/* Fixed Left Navigation */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main className="main-wrapper">
        <header className="top-bar">
          <div className="page-title">{getPageHeaderTitle()}</div>
          <div className="header-badges">
            <span className="chip info">Target MAPE: &lt; 15%</span>
            <span className="chip success">HDFS Storage: Healthy</span>
            <span className="chip" style={{ color: '#9ca3af' }}>FastAPI Backend :8000</span>
          </div>
        </header>

        <div className="content-body">
          {renderActivePage()}
        </div>
      </main>
    </div>
  );
}
