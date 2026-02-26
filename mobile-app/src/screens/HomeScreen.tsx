import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';

import { AlertItem } from '@/components/AlertItem';
import { AppContainer } from '@/components/AppContainer';
import { SectionCard } from '@/components/SectionCard';
import { TripCard } from '@/components/TripCard';
import { getTrip, getTripAlerts, listTrips, simulateThreat } from '@/services/tripService';
import { TripAlert, TripPlan } from '@/services/types';
import { notifyTripEvent } from '@/services/notifications';
import { useUiStore } from '@/store/uiStore';
import { colors } from '@/theme/colors';

export function HomeScreen() {
  const [loading, setLoading] = useState(false);
  const [plans, setPlans] = useState<TripPlan[]>([]);
  const [selectedTripId, setSelectedTripId] = useState<string>('');
  const [selectedPlan, setSelectedPlan] = useState<TripPlan | null>(null);
  const [alerts, setAlerts] = useState<TripAlert[]>([]);
  const initialLoadedRef = useRef(false);
  const lastNotifiedKeyRef = useRef<string>('');
  const pendingTripIdFromNotification = useUiStore((state) => state.pendingTripIdFromNotification);
  const consumePendingTripIdFromNotification = useUiStore((state) => state.consumePendingTripIdFromNotification);

  const selectedRisk = selectedPlan?.risk_level ?? 0;
  const riskLabel = useMemo(() => {
    if (selectedRisk >= 0.65) return 'High Risk';
    if (selectedRisk >= 0.35) return 'Medium Risk';
    return 'Stable';
  }, [selectedRisk]);

  const refreshAll = useCallback(async () => {
    try {
      setLoading(true);
      const fetchedPlans = await listTrips();
      setPlans(fetchedPlans);
      const nextTripId = selectedTripId || fetchedPlans[0]?.trip_id || '';
      setSelectedTripId(nextTripId);

      if (nextTripId) {
        const [tripRes, tripAlerts] = await Promise.all([getTrip(nextTripId), getTripAlerts(nextTripId)]);
        setSelectedPlan(tripRes.trip);
        setAlerts(tripAlerts);
        const priority = tripAlerts.find((item) => item.type === 'replan' || item.type === 'threat');
        if (priority && initialLoadedRef.current) {
          const key = `${priority.type}-${priority.at}-${priority.description}`;
          if (key !== lastNotifiedKeyRef.current) {
            lastNotifiedKeyRef.current = key;
            const title = priority.type === 'replan' ? 'Itinerary Updated' : 'Urban Disruption Detected';
            await notifyTripEvent(title, priority.description, nextTripId, priority.type);
          }
        }
        initialLoadedRef.current = true;
      } else {
        setSelectedPlan(null);
        setAlerts([]);
      }
    } catch (error: any) {
      Alert.alert('Refresh failed', error?.response?.data?.detail || error?.message || 'Unexpected error');
    } finally {
      setLoading(false);
    }
  }, [selectedTripId]);

  const selectTrip = async (tripId: string) => {
    try {
      setSelectedTripId(tripId);
      const [tripRes, tripAlerts] = await Promise.all([getTrip(tripId), getTripAlerts(tripId)]);
      setSelectedPlan(tripRes.trip);
      setAlerts(tripAlerts);
    } catch (error: any) {
      Alert.alert('Trip load failed', error?.response?.data?.detail || error?.message || 'Unexpected error');
    }
  };

  const triggerThreat = async () => {
    if (!selectedTripId) return;
    try {
      const correlationId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      await simulateThreat(selectedTripId, correlationId);
      await refreshAll();
      Alert.alert('Threat simulated', 'Mind agent will evaluate and eventually replan.');
    } catch (error: any) {
      Alert.alert('Threat simulation failed', error?.response?.data?.detail || error?.message || 'Unexpected error');
    }
  };

  useEffect(() => {
    refreshAll();
    const interval = setInterval(() => {
      refreshAll();
    }, 15000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  useEffect(() => {
    if (!pendingTripIdFromNotification) {
      return;
    }
    const targetTripId = consumePendingTripIdFromNotification();
    if (targetTripId) {
      selectTrip(targetTripId);
    }
  }, [pendingTripIdFromNotification]);

  return (
    <AppContainer>
      <SectionCard title="Realtime Trips" subtitle="Adaptive itineraries for dynamic urban contexts">
        <View style={styles.actions}>
          <Pressable style={styles.primaryBtn} onPress={refreshAll}><Text style={styles.primaryText}>Refresh</Text></Pressable>
          <Pressable style={styles.warnBtn} onPress={triggerThreat} disabled={!selectedTripId}><Text style={styles.warnText}>Simulate disruption</Text></Pressable>
        </View>
      </SectionCard>

      <SectionCard title="Your trips" subtitle={`Total: ${plans.length}`}>
        {loading ? <ActivityIndicator color={colors.primary} /> : null}
        {plans.length === 0 ? <Text style={styles.empty}>No trips yet. Create one from the Create tab.</Text> : null}
        <View style={styles.list}>
          {plans.map((plan) => (
            <TripCard key={plan.trip_id} plan={plan} selected={plan.trip_id === selectedTripId} onPress={() => selectTrip(plan.trip_id)} />
          ))}
        </View>
      </SectionCard>

      {selectedPlan ? (
        <SectionCard title={`${selectedPlan.city} · ${riskLabel}`} subtitle={`Status ${selectedPlan.status} · v${selectedPlan.version}`}>
          <FlatList
            data={selectedPlan.activities}
            keyExtractor={(item, index) => `${item.name}-${index}`}
            scrollEnabled={false}
            ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
            renderItem={({ item }) => (
              <View style={styles.activityItem}>
                <Text style={styles.activityTitle}>{item.name}</Text>
                <Text style={styles.activityMeta}>{new Date(item.starts_at).toLocaleString()} → {new Date(item.ends_at).toLocaleString()}</Text>
                <Text style={styles.activityMeta}>{item.address} · {item.transport_mode} · €{item.estimated_cost_eur.toFixed(2)}</Text>
              </View>
            )}
          />
        </SectionCard>
      ) : null}

      <SectionCard title="Live alerts" subtitle="Threat, assessments and replans">
        {alerts.length === 0 ? <Text style={styles.empty}>No alerts yet.</Text> : null}
        <View style={styles.list}>
          {alerts.slice(0, 12).map((item, index) => (
            <AlertItem key={`${item.type}-${item.at}-${index}`} alert={item} />
          ))}
        </View>
      </SectionCard>
    </AppContainer>
  );
}

const styles = StyleSheet.create({
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  primaryBtn: {
    flex: 1,
    borderRadius: 10,
    backgroundColor: colors.primary,
    paddingVertical: 10,
    alignItems: 'center',
  },
  primaryText: {
    color: colors.white,
    fontWeight: '700',
  },
  warnBtn: {
    flex: 1,
    borderRadius: 10,
    backgroundColor: colors.warning,
    paddingVertical: 10,
    alignItems: 'center',
  },
  warnText: {
    color: '#111827',
    fontWeight: '700',
  },
  empty: {
    color: colors.muted,
    fontSize: 13,
  },
  list: {
    gap: 8,
  },
  activityItem: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.cardSoft,
    padding: 10,
    gap: 3,
  },
  activityTitle: {
    color: colors.text,
    fontWeight: '700',
    fontSize: 14,
  },
  activityMeta: {
    color: colors.muted,
    fontSize: 12,
  },
});
