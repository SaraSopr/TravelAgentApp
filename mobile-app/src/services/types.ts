export type AuthPayload = {
  access_token: string;
  refresh_token?: string;
  token_type: 'bearer';
  user_id: string;
  username: string;
};

export type TripActivity = {
  name: string;
  category: string;
  address: string;
  starts_at: string;
  ends_at: string;
  transport_mode: string;
  estimated_cost_eur: number;
  notes?: string;
};

export type TripPlan = {
  trip_id: string;
  user_id: string;
  city: string;
  created_at: string;
  version: number;
  activities: TripActivity[];
  risk_level: number;
  budget_level: string;
  mobility_mode: string;
  interests: string[];
  status: string;
};

export type TripAlert = {
  type: 'threat' | 'assessment' | 'replan';
  at: string;
  confidence: number;
  description: string;
  source?: string;
  action?: string;
};
