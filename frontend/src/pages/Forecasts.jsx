import React, { useState, useEffect } from 'react';
import StoreSelector from '../components/StoreSelector';
import ForecastChart from '../components/ForecastChart';
import ForecastTable from '../components/ForecastTable';
import { fetchSales, fetchForecasts, triggerForecastRun } from '../api/api';

export default function Forecasts() {
  const [store, setStore] = useState(1);
  const [department, setDepartment] = useState(1);
  const [horizon, setHorizon] = useState(7);
  const [actuals, setActuals] = useState([]);
  const [forecasts, setForecasts] = useState([]);
  const [inventoryPlan, setInventoryPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    loadSeriesData(store, department);
  }, [store, department]);

  const loadSeriesData = async (sId, dId) => {
    try {
      setLoading(true);
      setErrorMsg('');
      const [salesRes, fcastRes] = await Promise.all([
        fetchSales(sId, dId, 25),
        fetchForecasts(sId, dId)
      ]);
      setActuals((salesRes || []).reverse());
      setForecasts(fcastRes || []);
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to load historical data for this store/dept.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunForecast = async () => {
    try {
      setLoading(true);
      setErrorMsg('');
      const payload = {
        store_id: store,
        department_id: department,
        horizon: horizon,
        lead_time: 2,
        service_level: 0.95
      };
      const res = await triggerForecastRun(payload);
      if (res && res.forecasts) {
        setForecasts(res.forecasts);
        setInventoryPlan(res.inventory_plan);
      }
    } catch (err) {
      console.error(err);
      setErrorMsg('Error generating ML forecast. Please ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 800 }}>Store & Department Demand Forecasting</h1>
        <p style={{ color: '#9ca3af', fontSize: '13px', marginTop: '4px' }}>
          Real-time dynamic multi-period forecasting powered by XGBoost with supply-chain safety stock buffers.
        </p>
      </div>

      {errorMsg && (
        <div style={{ background: 'rgba(244, 63, 94, 0.1)', color: '#f43f5e', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px', fontSize: '13px', border: '1px solid rgba(244, 63, 94, 0.3)' }}>
          {errorMsg}
        </div>
      )}

      {/* Selector Controls */}
      <StoreSelector
        selectedStore={store}
        setSelectedStore={setStore}
        selectedDept={department}
        setSelectedDept={setDepartment}
        horizon={horizon}
        setHorizon={setHorizon}
        onRunForecast={handleRunForecast}
        isLoading={loading}
      />

      {/* Visual Projections Chart */}
      <ForecastChart
        actuals={actuals}
        forecasts={forecasts}
        title={`Forecast Horizon for Store #${store} — Department #${department}`}
      />

      {/* Tabular Output & Safety Buffer */}
      <ForecastTable
        forecasts={forecasts}
        inventoryPlan={inventoryPlan}
      />
    </div>
  );
}
