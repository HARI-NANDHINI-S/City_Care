import axios from 'axios';
import {
  User,
  Issue,
  Department,
  AIAnalysisResult,
  MapPoint,
  AnalyticsDashboardData,
  IssueStatus,
  IssueType
} from '../types';

const API_BASE_URL = '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('civic_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  login: async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password });
    if (res.data.access_token) {
      localStorage.setItem('civic_token', res.data.access_token);
      localStorage.setItem('civic_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },
  register: async (data: { full_name: string; email: string; password: string; role?: string }) => {
    const res = await api.post('/auth/register', data);
    return res.data;
  },
  getMe: async () => {
    const res = await api.get('/auth/me');
    return res.data as User;
  },
  logout: () => {
    localStorage.removeItem('civic_token');
    localStorage.removeItem('civic_user');
  },
};

export const issueService = {
  analyzeImage: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post<AIAnalysisResult>('/issues/analyze-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
  createIssue: async (data: {
    title: string;
    description?: string;
    issue_type: string;
    latitude: number;
    longitude: number;
    address?: string;
    original_image_url: string;
    annotated_image_url?: string;
    ai_confidence: number;
    severity: string;
    priority_score: number;
    bounding_box_json?: string;
  }) => {
    const res = await api.post<Issue>('/issues', data);
    return res.data;
  },
  listIssues: async (params?: {
    status_filter?: string;
    type_filter?: string;
    dept_id?: number;
    min_priority?: number;
    search?: string;
  }) => {
    const res = await api.get<Issue[]>('/issues', { params });
    return res.data;
  },
  getMyReports: async () => {
    const res = await api.get<Issue[]>('/issues/my-reports');
    return res.data;
  },
  getMapData: async () => {
    const res = await api.get<MapPoint[]>('/issues/map-data');
    return res.data;
  },
  getIssueById: async (id: number) => {
    const res = await api.get<Issue>(`/issues/${id}`);
    return res.data;
  },
  updateStatus: async (id: number, status: string, notes?: string) => {
    const res = await api.patch<Issue>(`/issues/${id}/status`, { status, notes });
    return res.data;
  },
  assignDepartment: async (id: number, department_id: number, notes?: string) => {
    const res = await api.patch<Issue>(`/issues/${id}/assign`, { department_id, notes });
    return res.data;
  },
};

export const departmentService = {
  listDepartments: async () => {
    const res = await api.get<Department[]>('/departments');
    return res.data;
  },
};

export const analyticsService = {
  getDashboardStats: async () => {
    const res = await api.get<AnalyticsDashboardData>('/analytics/dashboard');
    return res.data;
  },
};

export const citizenService = {
  stats: async () => (await api.get('/issues/stats/citizen')).data,
  reports: async (params?: Record<string, string | number | undefined>) => (await api.get<Issue[]>('/issues/my-reports', { params })).data,
  details: async (id: number) => (await api.get<Issue>(`/issues/${id}`)).data,
  timeline: async (id: number) => (await api.get(`/issues/${id}/timeline`)).data,
};

export const officerService = {
  assigned: async () => (await api.get<Issue[]>('/issues/department/assigned')).data,
  accept: async (id:number) => (await api.post<Issue>(`/issues/${id}/accept`)).data,
  reject: async (id:number, reason:string) => (await api.post<Issue>(`/issues/${id}/reject`, {reason})).data,
  assign: async (id:number, officer_id:number) => (await api.post<Issue>(`/issues/${id}/assign`, {officer_id})).data,
  status: async (id:number, status:string, notes?:string) => (await api.patch<Issue>(`/issues/${id}/status`, {status, notes})).data,
  progress: async (id:number, progress_percentage:number, note?:string) => (await api.patch<Issue>(`/issues/${id}/progress`, {progress_percentage, note})).data,
  note: async (id:number, progress_percentage:number, note:string) => (await api.post<Issue>(`/issues/${id}/notes`, {progress_percentage, note})).data,
  estimate: async (id:number, estimated_completion_date:string) => (await api.patch<Issue>(`/issues/${id}/estimate`, {estimated_completion_date})).data,
  resolve: async (id:number) => (await api.post<Issue>(`/issues/${id}/resolve`)).data,
  close: async (id:number) => (await api.post<Issue>(`/issues/${id}/close`)).data,
};
