import api from './api';

export const authService = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', new URLSearchParams({
      username: email,
      password: password,
    }), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response;
  },

  register: async (email, password, name) => {
    const response = await api.post('/auth/register', {
      email,
      password,
      name,
    });
    return response;
  },

  verifyToken: async () => {
    const response = await api.get('/auth/me');
    return response;
  },

  updatePreferences: async (preferences) => {
    const response = await api.patch('/users/me/preferences', preferences);
    return response;
  },

  logout: () => {
    localStorage.removeItem('token');
  },
};
