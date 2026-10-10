import axios from 'axios';

// API client connected to FastAPI backend
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchDashboardSummary = async () => {
  const response = await apiClient.get('/api/dashboard/summary');
  return response.data;
};

export const fetchStores = async () => {
  const response = await apiClient.get('/api/stores');
  return response.data;
};

export const fetchStore = async (storeId) => {
  const response = await apiClient.get(`/api/stores/${storeId}`);
  return response.data;
};

export const fetchSales = async (storeId, departmentId, limit = 200) => {
  const params = { limit };
  if (storeId) params.store_id = storeId;
  if (departmentId) params.department_id = departmentId;
  const response = await apiClient.get('/api/sales', { params });
  return response.data;
};

export const fetchForecasts = async (storeId = 1, departmentId = 1) => {
  const response = await apiClient.get(`/api/forecasts/${storeId}/${departmentId}`);
  return response.data;
};

export const triggerForecastRun = async (payload) => {
  const response = await apiClient.post('/api/forecast/run', payload);
  return response.data;
};

export const fetchMetrics = async () => {
  const response = await apiClient.get('/api/metrics');
  return response.data;
};

export const fetchInventoryRecommendations = async () => {
  const response = await apiClient.get('/api/inventory/recommendations');
  return response.data;
};

export default apiClient;
