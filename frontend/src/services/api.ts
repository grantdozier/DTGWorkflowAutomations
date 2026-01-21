import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const register = (data: { email: string; password: string; name: string; company_name: string }) =>
  api.post('/auth/register', data);

export const login = (email: string, password: string) => {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  return api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
};

export const getCurrentUser = () => api.get('/auth/me');

// Projects
export const getProjects = () => api.get('/projects');
export const getProject = (id: string) => api.get(`/projects/${id}`);
export const createProject = (data: any) => api.post('/projects', data);

// Documents
export const uploadDocument = (projectId: string, file: File, docType: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('doc_type', docType);
  return api.post(`/projects/${projectId}/documents`, formData);
};

export const getDocuments = (projectId: string) => api.get(`/projects/${projectId}/documents`);

// AI Parsing
export const parseDocument = (projectId: string, documentId: string) =>
  api.post(`/ai/projects/${projectId}/documents/${documentId}/parse-and-save?max_pages=5`);

// Estimation
export const generateEstimate = (projectId: string) =>
  api.post(`/projects/${projectId}/estimate`, { include_takeoffs: true });

export const getEstimates = (projectId: string) => api.get(`/projects/${projectId}/estimates`);
export const getEstimate = (projectId: string, estimateId: string) =>
  api.get(`/projects/${projectId}/estimates/${estimateId}`);

export default api;
