import api from './api';

export const budgetService = {
  getAllBudgets: async (params = {}) => {
    const response = await api.get('/budgets', { params });
    return response;
  },

  getBudgetById: async (id) => {
    const response = await api.get(`/budgets/${id}`);
    return response;
  },

  createBudget: async (budgetData) => {
    const response = await api.post('/budgets', budgetData);
    return response;
  },

  updateBudget: async (id, budgetData) => {
    const response = await api.put(`/budgets/${id}`, budgetData);
    return response;
  },

  deleteBudget: async (id) => {
    const response = await api.delete(`/budgets/${id}`);
    return response;
  },
};