import { create } from 'zustand';

import { AuthPayload } from '@/services/types';

type AuthState = {
  accessToken: string;
  refreshToken: string;
  userId: string;
  username: string;
  isHydrated: boolean;
  setSession: (payload: AuthPayload) => void;
  clearSession: () => void;
  markHydrated: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: '',
  refreshToken: '',
  userId: '',
  username: '',
  isHydrated: false,
  setSession: (payload) =>
    set(() => ({
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token ?? '',
      userId: payload.user_id,
      username: payload.username,
      isHydrated: true,
    })),
  clearSession: () =>
    set(() => ({
      accessToken: '',
      refreshToken: '',
      userId: '',
      username: '',
      isHydrated: true,
    })),
  markHydrated: () => set(() => ({ isHydrated: true })),
}));
