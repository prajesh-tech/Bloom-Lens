import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ApiErrorBody {
  error_code?: string;
  message?: string;
  status_code?: number;
  timestamp?: string;
  detail?: unknown;
}

export class ApiError extends Error {
  errorCode?: string;
  statusCode?: number;
  timestamp?: string;

  constructor(message: string, body?: ApiErrorBody) {
    super(message);
    this.name = 'ApiError';
    this.errorCode = body?.error_code;
    this.statusCode = body?.status_code;
    this.timestamp = body?.timestamp;
  }
}

const API_KEY = import.meta.env.VITE_API_KEY;

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
  },
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const body = error.response?.data as ApiErrorBody | undefined;
    const detailMessage =
      typeof body?.detail === 'string'
        ? body.detail
        : body?.detail && typeof body.detail === 'object' && 'message' in body.detail
          ? String((body.detail as { message?: unknown }).message)
          : undefined;
    const message =
      body?.message ||
      detailMessage ||
      error.message ||
      'An unexpected API error occurred.';
    return Promise.reject(new ApiError(message, body));
  }
);
