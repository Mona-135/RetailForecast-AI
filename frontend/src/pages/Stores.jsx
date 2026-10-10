import React, { useState, useEffect } from 'react';
import { fetchStores, fetchSales } from '../api/api';

export default function Stores() {
  const [stores, setStores] = useState([]);
  const [selectedStore, setSelectedStore] = useState(1);
  const [storeSales, setStoreSales] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStores();
  }, []);

  useEffect(() => {
    if (selectedStore) {
      loadStoreSales(selectedStore);
    }
  }, [selectedStore]);

  const loadStores = async () => {
    try {
      const res = await fetchStores();
      setStores(res || []);
    } catch (err) {
      console.error(err);
      // Fallback
      setStores([
        { id: 1, store_id: 1, store_type: 'A', size: 151315 },
        { id: 2, store_id: 2, store_type: 'A', size: 202307 },
        { id: 3, store_id: 3, store_type: 'B', size: 37392 },
        { id: 4, store_id: 4, store_type: 'A', size: 205863 },
        { id: 5, store_id: 5, store_type: 'B', size: 34875 }
      ]);
    }
  };

  const loadStoreSales = async (sId) => {
    try {
      setLoading(true);
      const res = await fetchSales(sId, null, 15);
      setStoreSales(res || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 800 }}>Retail Fleet Stores</h1>
        <p style={{ color: '#9ca3af', fontSize: '13px', marginTop: '4px' }}>
          Overview of physical retail store footprints, square footage, classifications, and transaction activity.
        </p>
      </div>

      {/* Store Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '28px' }}>
        {stores.map((s) => (
          <div
            key={s.store_id}
            className="glass-card"
            style={{
              cursor: 'pointer',
              borderColor: selectedStore === s.store_id ? '#3b82f6' : 'rgba(255,255,255,0.08)',
              background: selectedStore === s.store_id ? 'rgba(59, 130, 246, 0.12)' : 'var(--bg-card)'
            }}
            onClick={() => setSelectedStore(s.store_id)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '16px', fontWeight: 700 }}>Store #{s.store_id}</span>
              <span className="chip info">Type {s.store_type}</span>
            </div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#f9fafb' }}>
              {Number(s.size).toLocaleString()} <span style={{ fontSize: '12px', color: '#9ca3af' }}>sq.ft</span>
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '6px' }}>
              Classification: Supercenter Format
            </div>
          </div>
        ))}
      </div>

      {/* Selected Store Recent Activity */}
      <div className="glass-card">
        <div className="chart-header">
          <div>
            <div className="chart-title">Recent Sales Activity for Store #{selectedStore}</div>
            <div className="chart-subtitle">Cross-departmental records synchronized with PostgreSQL</div>
          </div>
        </div>

        {loading ? (
          <div className="loading-container"><div className="spinner"></div></div>
        ) : (
          <table className="custom-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Store</th>
                <th>Department</th>
                <th>Sales Volume ($)</th>
                <th>Holiday Week</th>
              </tr>
            </thead>
            <tbody>
              {storeSales.map((r, i) => (
                <tr key={i}>
                  <td>{r.sales_date}</td>
                  <td>Store #{r.store_id}</td>
                  <td>Dept #{r.department_id}</td>
                  <td style={{ fontWeight: 600, color: '#f9fafb' }}>
                    ${Number(r.sales).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td>
                    {r.is_holiday ? (
                      <span className="status-pill overstock">HOLIDAY SPIKE</span>
                    ) : (
                      <span style={{ color: '#6b7280' }}>Regular</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
