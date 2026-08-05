const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api/v1';

export type ApiError = {
  detail?: string;
  message?: string;
};

function getStoredToken() {
  return typeof window === 'undefined' ? null : window.localStorage.getItem('growthos_token');
}

function buildHeaders(token?: string, extra?: HeadersInit, hasFormData = false): HeadersInit {
  const headers = new Headers(extra || {});
  if (!hasFormData) headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return headers;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: buildHeaders(token || undefined, options.headers, options.body instanceof FormData),
  });

  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('growthos_token');
    }
    throw new Error('登录状态已失效，请重新登录');
  }

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as ApiError | null;
    throw new Error(errorBody?.detail || errorBody?.message || '请求失败');
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function setStoredToken(token: string) {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem('growthos_token', token);
  }
}

export function clearStoredToken() {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem('growthos_token');
  }
}
