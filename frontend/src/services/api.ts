import axios from 'axios';
import { auth } from '@/lib/firebase';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
  timeout: 10000,
});

apiClient.interceptors.request.use(async (config) => {
  try {
    const token = await auth.currentUser?.getIdToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch (error) {
    console.error('Failed to get auth token:', error);
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout - backend may be offline');
    } else if (error.code === 'ERR_NETWORK') {
      console.error('Network error - backend connection failed');
    } else if (error.response?.status === 401) {
      auth.signOut();
    }
    return Promise.reject(error);
  }
);

export default apiClient;
