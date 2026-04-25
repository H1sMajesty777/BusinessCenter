import api from './api';

export const getAuditLogs = async (limit = 100) => {
  const response = await api.get(`/audit?limit=${limit}`);
  return response.data;
};

export const getAuditStats = async () => {
  const response = await api.get('/audit/stats');
  return response.data;
};