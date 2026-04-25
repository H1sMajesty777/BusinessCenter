import api from './api';

// Получить свои заявки
export const getMyApplications = async () => {
  const response = await api.get('/applications/my');
  return response.data;
};

// Создать заявку
export const createApplication = async (officeId, desiredDate, comment) => {
  const response = await api.post('/applications', {
    office_id: officeId,
    desired_date: desiredDate,
    comment
  });
  return response.data;
};

// Обновить статус заявки (для менеджера/админа)
export const updateApplicationStatus = async (applicationId, statusId) => {
  const response = await api.put(`/applications/${applicationId}/status`, { status_id: statusId });
  return response.data;
};