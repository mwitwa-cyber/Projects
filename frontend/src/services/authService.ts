import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1/auth';

export const authService = {
  async login(username: string, password: string, totp_code?: string) {
    const response = await axios.post(`${API_URL}/login`, {
      username,
      password,
      totp_code
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
  },

  async setupTOTP() {
    const token = this.getToken();
    const response = await axios.post(`${API_URL}/totp/setup`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async verifyTOTP(code: string) {
    const token = this.getToken();
    const response = await axios.post(`${API_URL}/totp/verify`, { code }, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async disableTOTP(code: string) {
    const token = this.getToken();
    const response = await axios.post(`${API_URL}/totp/disable`, { code }, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};
