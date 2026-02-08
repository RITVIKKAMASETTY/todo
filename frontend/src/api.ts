import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  register: (username: string, email: string, password: string) =>
    api.post('/auth/register', { username, email, password }),

  login: (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },

  getMe: () => api.get('/auth/me'),

  getMeWithToken: (token: string) => api.get('/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  }),
};

// Game API
export const gameAPI = {
  findMatch: () => api.post('/game/find-match'),
  getGame: (gameId: number) => api.get(`/game/${gameId}`),
  getGameState: (gameId: number) => api.get(`/game/${gameId}/state`),
  getGameHistory: (gameId: number) => api.get(`/game/${gameId}/history`),
};

// Leaderboard API
export const leaderboardAPI = {
  getLeaderboard: (limit = 10) => api.get(`/leaderboard?limit=${limit}`),
  getMyRank: () => api.get('/leaderboard/me'),
};

export default api;
