import React from 'react';

export default function KPICard({ label, value, subtext, statusType, icon }) {
  const getStatusChip = () => {
    if (!statusType) return null;
    if (statusType === 'success') {
      return <span className="chip success">TARGET ACHIEVED</span>;
    }
    if (statusType === 'danger') {
      return <span className="chip warning">TARGET PENDING</span>;
    }
    if (statusType === 'info') {
      return <span className="chip info">{subtext || 'ACTIVE'}</span>;
    }
    return null;
  };

  return (
    <div className="kpi-card">
      <div className="kpi-header">
        <span className="kpi-label">{label}</span>
        {icon && <span style={{ fontSize: '18px' }}>{icon}</span>}
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-footer">
        {getStatusChip()}
        {subtext && !statusType && <span>{subtext}</span>}
      </div>
    </div>
  );
}
