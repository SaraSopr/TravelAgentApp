import Constants from 'expo-constants';
import axios from 'axios';

import { clearSessionStorage, saveSession } from '@/services/storage';
import { AuthPayload } from '@/services/types';
import { useAuthStore } from '@/store/authStore';

const configuredApiBaseUrl =
  (Constants.expoConfig?.extra?.apiBaseUrl as string | undefined) ||
  'http://127.0.0.1:8000/api';

function resolveApiBaseUrl() {
  const usesLoopback = /localhost|127\.0\.0\.1/.test(configuredApiBaseUrl);
  if (!usesLoopback) {
    return configuredApiBaseUrl;
  }

  const hostUri = Constants.expoConfig?.hostUri;
  if (!hostUri) {
    return configuredApiBaseUrl;
  }

  const host = hostUri.split(':')[0];
  if (!host) {
    return configuredApiBaseUrl;
  }

  return `http://${host}:8000/api`;
}

const apiBaseUrl = resolveApiBaseUrl();

export const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshingPromise: Promise<boolean> | null = null;

async function refreshSessionToken(): Promise<boolean> {
  const state = useAuthStore.getState();
  if (!state.refreshToken) {
    return false;
  }

  try {
    const response = await axios.post<AuthPayload>(`${apiBaseUrl}/auth/refresh`, {
      refresh_token: state.refreshToken,
    });
    useAuthStore.getState().setSession(response.data);
    await saveSession(
      response.data.access_token,
      response.data.refresh_token ?? '',
      response.data.user_id,
      response.data.username,
    );
    return true;
  } catch {
    useAuthStore.getState().clearSession();
    await clearSessionStorage();
    return false;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalConfig = error?.config;
    if (!originalConfig || originalConfig._retry) {
      return Promise.reject(error);
    }

    if (error?.response?.status === 401) {
      originalConfig._retry = true;
      if (!refreshingPromise) {
        refreshingPromise = refreshSessionToken();
      }
      const refreshed = await refreshingPromise;
      refreshingPromise = null;

      if (refreshed) {
        return api(originalConfig);
      }
    }
    return Promise.reject(error);
  },
);
