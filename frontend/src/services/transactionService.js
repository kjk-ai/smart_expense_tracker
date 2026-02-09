import api from './api';

export const transactionService = {
  getAllTransactions: async (params = {}) => {
    const response = await api.get('/transactions', { params });
    return response;
  },

  getTransactionById: async (id) => {
    const response = await api.get(`/transactions/${id}`);
    return response;
  },

  createTransaction: async (transactionData) => {
    const response = await api.post('/transactions', transactionData);
    return response;
  },

  updateTransaction: async (id, transactionData) => {
    const response = await api.put(`/transactions/${id}`, transactionData);
    return response;
  },

  deleteTransaction: async (id) => {
    const response = await api.delete(`/transactions/${id}`);
    return response;
  },

  getTransactionStats: async (params = {}) => {
    const response = await api.get('/stats/transactions', { params });
    return response;
  },
};
