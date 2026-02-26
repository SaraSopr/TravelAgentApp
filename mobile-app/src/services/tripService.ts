import { api } from '@/services/api';
import { TripAlert, TripPlan } from '@/services/types';

export type CreateTripInput = {
  city: string;
  intent: string;
  start_time: string;
  budget_level: 'low' | 'medium' | 'high';
  mobility_mode: 'walk' | 'public_transport' | 'taxi';
  interests: string[];
};

export async function createTrip(input: CreateTripInput) {
  const response = await api.post<{ status: string; correlation_id: string }>('/trips', input);
  return response.data;
}

export async function listTrips() {
  const response = await api.get<{ plans: TripPlan[] }>('/trips');
  return response.data.plans;
}

export async function getTrip(tripId: string) {
  const response = await api.get<{ found: boolean; trip: TripPlan | null }>(`/trips/${tripId}`);
  return response.data;
}

export async function getTripAlerts(tripId: string) {
  const response = await api.get<{ alerts: TripAlert[] }>(`/trips/${tripId}/alerts`);
  return response.data.alerts;
}

export async function simulateThreat(tripId: string, correlationId: string) {
  await api.post(`/threats/simulate?trip_id=${encodeURIComponent(tripId)}&correlation_id=${encodeURIComponent(correlationId)}`);
}
