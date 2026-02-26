import { Pressable, StyleSheet, Text, View } from 'react-native';

import { TripPlan } from '@/services/types';
import { colors } from '@/theme/colors';

type Props = {
  plan: TripPlan;
  selected?: boolean;
  onPress: () => void;
};

export function TripCard({ plan, selected, onPress }: Props) {
  const riskColor = plan.risk_level >= 0.65 ? colors.danger : plan.risk_level >= 0.35 ? colors.warning : colors.success;

  return (
    <Pressable style={[styles.card, selected && styles.selected]} onPress={onPress}>
      <View style={styles.rowBetween}>
        <Text style={styles.city}>{plan.city}</Text>
        <Text style={[styles.badge, { color: riskColor }]}>Risk {plan.risk_level.toFixed(2)}</Text>
      </View>
      <Text style={styles.meta}>v{plan.version} · {plan.status} · {plan.activities.length} activities</Text>
      <Text style={styles.meta}>{plan.budget_level} · {plan.mobility_mode}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.cardSoft,
    padding: 12,
    gap: 4,
  },
  selected: {
    borderColor: colors.primary,
    backgroundColor: '#1D2E4F',
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  city: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '700',
  },
  badge: {
    fontSize: 12,
    fontWeight: '700',
  },
  meta: {
    color: colors.muted,
    fontSize: 12,
  },
});
