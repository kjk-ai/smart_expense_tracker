import api from './api';

export const holidayService = {
  getHolidays: async ({ country, from, to } = {}) => {
    const params = {};
    if (country) params.country = country;
    if (from) params.from = from;
    if (to) params.to = to;
    const response = await api.get('/holidays', { params });
    return response;
  },

  getHolidayInsights: async ({ windowDays = 30, force = false } = {}) => {
    const response = await api.get('/insights/holidays', {
      params: {
        window_days: windowDays,
        force
      }
    });
    return response;
  }
};
