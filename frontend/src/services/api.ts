import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { supabase } from '../lib/supabase';

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    // Try to get Supabase session first
    const { data: { session } } = await supabase.auth.getSession();
    console.log('[API Interceptor] Supabase session:', session ? 'Found' : 'Not found');
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
      console.log('[API Interceptor] Added Supabase token to request');
    } else {
      // Fall back to legacy token if no Supabase session
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('[API Interceptor] Added legacy token to request');
      } else {
        console.log('[API Interceptor] No auth token found');
      }
    }
    
    // Add organization/project headers if they exist
    const orgId = localStorage.getItem('currentOrganizationId');
    const projectId = localStorage.getItem('currentProjectId');
    
    if (orgId) {
      config.headers['X-Organization-ID'] = orgId;
    }
    if (projectId) {
      config.headers['X-Project-ID'] = projectId;
    }
    
    console.log('[API Interceptor] Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh token
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await axios.post('/auth/refresh', {
            refresh_token: refreshToken
          });
          
          const { access_token } = response.data;
          localStorage.setItem('accessToken', access_token);
          
          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors
    if (error.response?.status === 403) {
      // Forbidden - user doesn't have permission
      console.error('Permission denied:', error.response.data);
    } else if (error.response?.status === 404) {
      // Not found
      console.error('Resource not found:', error.response.data);
    } else if (error.response?.status === 500) {
      // Server error
      console.error('Server error:', error.response.data);
    }

    return Promise.reject(error);
  }
);

// API service methods
export const apiService = {
  // Auth endpoints
  auth: {
    login: (email: string, password: string) => 
      api.post('/auth/login', { email, password }),
    
    signup: (data: { email: string; password: string; name: string; organization_name: string }) =>
      api.post('/auth/signup', data),
    
    logout: () => api.post('/auth/logout'),
    
    getMe: () => api.get('/auth/me'),
    
    refresh: () => api.post('/auth/refresh'),
  },

  // Organization endpoints
  organizations: {
    list: () => api.get('/api/organizations'),
    
    create: (data: { name: string; description?: string }) =>
      api.post('/api/organizations', data),
    
    get: (id: string) => api.get(`/api/organizations/${id}`),
    
    update: (id: string, data: any) => api.put(`/api/organizations/${id}`, data),
    
    delete: (id: string) => api.delete(`/api/organizations/${id}`),
    
    getMembers: (id: string) => api.get(`/api/organizations/${id}/members`),
    
    inviteMember: (id: string, data: { email: string; role: string }) =>
      api.post(`/api/organizations/${id}/members`, data),
    
    removeMember: (orgId: string, memberId: string) =>
      api.delete(`/api/organizations/${orgId}/members/${memberId}`),
    
    updateMemberRole: (orgId: string, memberId: string, data: { role: string }) =>
      api.put(`/api/organizations/${orgId}/members/${memberId}`, data),
    
    getUsage: (id: string) =>
      api.get(`/api/organizations/${id}/usage`),
  },

  // Project endpoints
  projects: {
    list: (organizationId?: string) => 
      api.get('/api/projects', { params: { organization_id: organizationId } }),
    
    create: (data: { name: string; description?: string; organization_id: string }) =>
      api.post('/api/projects', data),
    
    get: (id: string) => api.get(`/api/projects/${id}`),
    
    update: (id: string, data: any) => api.put(`/api/projects/${id}`, data),
    
    delete: (id: string) => api.delete(`/api/projects/${id}`),
    
    getMembers: (id: string) => api.get(`/api/projects/${id}/members`),
    
    addMember: (id: string, data: { user_id: string; role: string }) =>
      api.post(`/api/projects/${id}/members`, data),
  },

  // Q&A endpoints
  qa: {
    askQuestion: (question: string) => 
      api.post('/api/ask-question', { question }),
    
    getInteractions: () => api.get('/api/qa-interactions'),
    
    submitFeedback: (interactionId: string, feedback: any) =>
      api.post(`/api/qa-interactions/${interactionId}/feedback`, feedback),
    
    getKnowledgeOverview: () => api.get('/api/knowledge-overview'),
  },

  // Affirmations endpoints
  affirmations: {
    generate: (data: { period_name: string; count?: number; period_info?: any }) =>
      api.post('/generate-affirmations', data),
    
    list: (period?: string) => 
      api.get('/affirmations', { params: { period_name: period } }),
    
    getPeriods: () => api.get('/periods'),
  },

  // Content endpoints
  content: {
    generate: (data: any) => api.post('/content/generate', data),
    
    get: (id: string) => api.get(`/content/${id}`),
    
    list: () => api.get('/content'),
    
    approve: (id: string, approved: boolean, feedback?: string) =>
      api.post('/content/approve', { content_id: id, approved, feedback }),
    
    delete: (id: string) => api.delete(`/content/${id}`),
  },

  // Workflow endpoints
  workflows: {
    create: (data: { period: string; workflow_type?: string; options?: any }) =>
      api.post('/api/workflows', data),
    
    list: () => api.get('/api/workflows'),
    
    get: (id: string) => api.get(`/api/workflows/${id}`),
    
    delete: (id: string) => api.delete(`/api/workflows/${id}`),
    
    getTemplates: () => api.get('/api/workflow-templates'),
  },

  // Visual posts endpoints
  visualPosts: {
    searchImages: (tags: string[], period: string, count?: number) =>
      api.post('/search-images', { tags, period, count }),
    
    create: (data: any) => api.post('/create-visual-post', data),
    
    list: (period?: string) => 
      api.get('/visual-posts', { params: { period } }),
    
    delete: (id: string) => api.delete(`/visual-posts/${id}`),
  },

  // Instagram endpoints
  instagram: {
    generatePost: (data: any) => api.post('/instagram-posts/generate', data),
    
    listPosts: () => api.get('/instagram-posts'),
    
    schedulePost: (data: any) => api.post('/instagram-posts/schedule', data),
    
    analyzeProfile: (username: string) =>
      api.post('/api/analyze-instagram-profile', { username }),
    
    prepareContent: (data: { instagram_post_id: string; visual_post_id?: string }) =>
      api.post('/prepare-instagram-content', data),
    
    postToInstagram: (data: { instagram_post_id: string; visual_post_id?: string; post_type?: string }) =>
      api.post('/post-to-instagram', data),
  },
};

export default api;