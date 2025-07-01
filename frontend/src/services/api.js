import axios from 'axios';

const API_URL = 'http://localhost:8000/api'; // Assuming the Django backend is running on port 8000

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getArticles = (params) => {
  return apiClient.get('/articles/', { params });
};

export const searchArticles = (params) => {
  return apiClient.get('/articles/search/', { params });
};

export const getCategories = () => {
  return apiClient.get('/categories/');
};

export const getTasks = () => {
  return apiClient.get('/tasks/');
};

export const startScraping = (data) => {
  return apiClient.post('/start/', data);
};
