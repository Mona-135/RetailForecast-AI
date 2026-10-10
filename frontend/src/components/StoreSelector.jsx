import React from 'react';

export default function StoreSelector({
  stores = [1, 2, 3, 4, 5],
  departments = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  selectedStore,
  setSelectedStore,
  selectedDept,
  setSelectedDept,
  horizon,
  setHorizon,
  onRunForecast,
  isLoading
}) {
  return (
    <div className="controls-bar">
      <div>
        <label style={{ fontSize: '11px', color: '#9ca3af', display: 'block', marginBottom: '4px', textTransform: 'uppercase' }}>
          Select Store
        </label>
        <select
          className="custom-select"
          value={selectedStore}
          onChange={(e) => setSelectedStore(Number(e.target.value))}
        >
          {stores.map((s) => (
            <option key={s} value={s}>
              Store #{s}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label style={{ fontSize: '11px', color: '#9ca3af', display: 'block', marginBottom: '4px', textTransform: 'uppercase' }}>
          Department
        </label>
        <select
          className="custom-select"
          value={selectedDept}
          onChange={(e) => setSelectedDept(Number(e.target.value))}
        >
          {departments.map((d) => (
            <option key={d} value={d}>
              Department #{d}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label style={{ fontSize: '11px', color: '#9ca3af', display: 'block', marginBottom: '4px', textTransform: 'uppercase' }}>
          Forecast Horizon
        </label>
        <select
          className="custom-select"
          value={horizon}
          onChange={(e) => setHorizon(Number(e.target.value))}
        >
          <option value={7}>7 Periods</option>
          <option value={14}>14 Periods</option>
          <option value={28}>28 Periods</option>
        </select>
      </div>

      <div style={{ marginTop: 'auto' }}>
        <button
          className="btn-primary"
          onClick={onRunForecast}
          disabled={isLoading}
        >
          {isLoading ? 'Computing ML Forecast...' : '⚡ Run ML Forecast'}
        </button>
      </div>
    </div>
  );
}
