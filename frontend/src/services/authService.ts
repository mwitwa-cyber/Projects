import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = `${API_BASE_URL}/api/v1/auth`;

// Session storage key
const USER_STORAGE_KEY = 'luse_auth_user';

export const authService = {
  async login(username: string, password: string, totp_code?: string) {
    const response = await axios.post(`${API_URL}/login`, {
      username: username.toLowerCase().trim(),
      password,
      totp_code
    });
    if (response.data.access_token) {
      // Store in sessionStorage instead of localStorage for better security
      // Token is cleared when browser tab is closed
      sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify({
        access_token: response.data.access_token,
        token_type: response.data.token_type,
        username: response.data.username,
        totp_enabled: response.data.totp_enabled
      }));
    }
    return response.data;
  },

  async register(username: string, email: string, password: string) {
    const response = await axios.post(`${API_URL}/register`, {
      username: username.toLowerCase().trim(),
      email: email.toLowerCase().trim(),
      password,
    });
    return response.data;
  },

  logout() {
    sessionStorage.removeItem(USER_STORAGE_KEY);
    // Also clear localStorage in case of migration
    localStorage.removeItem('user');
  },

  getCurrentUser() {
    // Check sessionStorage first, then localStorage for backwards compatibility
    const userStr = sessionStorage.getItem(USER_STORAGE_KEY) || localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
    return null;
  },

  getToken(): string | null {
    const user = this.getCurrentUser();
    return user?.access_token || null;
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },

  async setupTOTP() {
    const token = this.getToken();
    if (!token) throw new Error('Not authenticated');

    const response = await axios.post(`${API_URL}/totp/setup`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async verifyTOTP(code: string) {
    const token = this.getToken();
    if (!token) throw new Error('Not authenticated');

    const response = await axios.post(`${API_URL}/totp/verify`, { code }, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async disableTOTP(code: string) {
    const token = this.getToken();
    if (!token) throw new Error('Not authenticated');

    const response = await axios.post(`${API_URL}/totp/disable`, { code }, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};
