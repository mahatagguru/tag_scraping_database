import axios from 'axios';
import {
  Category,
  Year,
  Set,
  Card,
  Grade,
  Population,
  DashboardStats,
  SearchResult,
  PopulationTrends,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Health check
export const healthCheck = async (): Promise<{ status: string; database?: string }> => {
  const response = await api.get('/health');
  return response.data;
};

// Dashboard
export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await api.get('/dashboard');
  return response.data;
};

// Categories
export const getCategories = async (
  activeOnly: boolean = true,
  limit: number = 100,
  offset: number = 0
): Promise<Category[]> => {
  const response = await api.get('/categories', {
    params: { active_only: activeOnly, limit, offset },
  });
  return response.data;
};

// Years
export const getYearsByCategory = async (
  categoryId: number,
  activeOnly: boolean = true,
  limit: number = 100,
  offset: number = 0
): Promise<Year[]> => {
  const response = await api.get(`/categories/${categoryId}/years`, {
    params: { active_only: activeOnly, limit, offset },
  });
  return response.data;
};

// Sets
export const getSetsByYear = async (
  yearId: number,
  activeOnly: boolean = true,
  limit: number = 100,
  offset: number = 0
): Promise<Set[]> => {
  const response = await api.get(`/years/${yearId}/sets`, {
    params: { active_only: activeOnly, limit, offset },
  });
  return response.data;
};

// Cards
export const getCardsBySet = async (
  setId: number,
  activeOnly: boolean = true,
  limit: number = 100,
  offset: number = 0,
  search?: string
): Promise<Card[]> => {
  const response = await api.get(`/sets/${setId}/cards`, {
    params: { active_only: activeOnly, limit, offset, search },
  });
  return response.data;
};

// Populations
export const getCardPopulations = async (
  cardUid: string,
  limit: number = 100,
  offset: number = 0
): Promise<Population[]> => {
  const response = await api.get(`/cards/${cardUid}/populations`, {
    params: { limit, offset },
  });
  return response.data;
};

// Grades
export const getGrades = async (
  activeOnly: boolean = true,
  limit: number = 100
): Promise<Grade[]> => {
  const response = await api.get('/grades', {
    params: { active_only: activeOnly, limit },
  });
  return response.data;
};

// Search
export const search = async (
  query: string,
  limit: number = 50
): Promise<SearchResult[]> => {
  const response = await api.get('/search', {
    params: { q: query, limit },
  });
  return response.data;
};

// Analytics
export const getPopulationTrends = async (
  cardUid?: string,
  gradeLabel?: string,
  days: number = 30
): Promise<PopulationTrends> => {
  const response = await api.get('/analytics/population-trends', {
    params: { card_uid: cardUid, grade_label: gradeLabel, days },
  });
  return response.data;
};

export default api;
