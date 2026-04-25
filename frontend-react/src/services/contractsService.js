import api from './api';

export const getMyContracts = async () => {
  const response = await api.get('/contracts/my');
  return response.data;
};

export const getAllContracts = async () => {
  const response = await api.get('/contracts');
  return response.data;
};

export const createContract = async (contractData) => {
  const response = await api.post('/contracts', contractData);
  return response.data;
};