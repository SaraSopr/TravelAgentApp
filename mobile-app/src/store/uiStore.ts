import { create } from 'zustand';

type UiState = {
  pendingTripIdFromNotification: string;
  setPendingTripIdFromNotification: (tripId: string) => void;
  consumePendingTripIdFromNotification: () => string;
};

export const useUiStore = create<UiState>((set, get) => ({
  pendingTripIdFromNotification: '',
  setPendingTripIdFromNotification: (tripId) =>
    set(() => ({ pendingTripIdFromNotification: tripId })),
  consumePendingTripIdFromNotification: () => {
    const tripId = get().pendingTripIdFromNotification;
    set(() => ({ pendingTripIdFromNotification: '' }));
    return tripId;
  },
}));
