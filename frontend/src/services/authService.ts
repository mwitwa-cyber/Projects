import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1/auth';

export const authService = {
  async login(username: string, password: string) {
    const response = await axios.post(`${API_URL}/login`, {
      username,
      password
    });
    if (response.data.access_token) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  },

  async register(username: string, email: string, password: string) {
    const response = await axios.post(`${API_URL}/register`, {
      username,
      email,
      password,
    });
    return response.data;
  },

  logout() {
    localStorage.removeItem('user');
  },

  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      return JSON.parse(userStr);
    }
    return null;
  },

  getToken() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      return user?.access_token;
    }
    return null;
  }
};
