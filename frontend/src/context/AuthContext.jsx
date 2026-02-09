import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token and fetch user data
      const verifyToken = async () => {
        try {
          const response = await authService.verifyToken();
          setUser(response.data);
        } catch (error) {
          localStorage.removeItem('token');
        } finally {
          setLoading(false);
        }
      };
      verifyToken();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authService.login(email, password);
      const { access_token, token_type } = response.data;
      localStorage.setItem('token', access_token);
      
      // Fetch user data after login
      const userResponse = await authService.verifyToken();
      setUser(userResponse.data);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = error.response?.data?.detail || 'Login failed';
      return { success: false, error: errorMessage };
    }
  };

  const register = async (email, password, name) => {
    try {
      const response = await authService.register(email, password, name);
      const userData = response.data;
      
      // After register, we need to login to get the token
      const loginResponse = await authService.login(email, password);
      const { access_token, token_type } = loginResponse.data;
      const token = `${token_type} ${access_token}`;
      localStorage.setItem('token', access_token);
      
      setUser(userData);
      return { success: true };
    } catch (error) {
      console.error('Register error:', error);
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      return { success: false, error: errorMessage };
    }
  };

  const updatePreferences = async (preferences) => {
    try {
      const response = await authService.updatePreferences(preferences);
      setUser(response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Update preferences error:', error);
      const errorMessage = error.response?.data?.detail || 'Update failed';
      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value = {
    user,
    login,
    register,
    updatePreferences,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
