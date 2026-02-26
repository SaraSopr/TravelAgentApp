import { api } from '@/services/api';
import { AuthPayload } from '@/services/types';

export async function register(username: string, password: string) {
  const response = await api.post<AuthPayload>('/auth/register', { username, password });
  return response.data;
}

export async function login(username: string, password: string) {
  const response = await api.post<AuthPayload>('/auth/login', { username, password });
  return response.data;
}

export async function logout(refreshToken: string) {
  await api.post('/auth/logout', { refresh_token: refreshToken });
}
