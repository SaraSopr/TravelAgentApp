import { StyleSheet, Text, View } from 'react-native';

import { TripAlert } from '@/services/types';
import { colors } from '@/theme/colors';

type Props = {
  alert: TripAlert;
};

export function AlertItem({ alert }: Props) {
  const borderColor = alert.type === 'replan' ? colors.success : alert.type === 'assessment' ? colors.primary : colors.warning;

  return (
    <View style={[styles.card, { borderLeftColor: borderColor }]}> 
      <Text style={styles.type}>{alert.type.toUpperCase()}</Text>
      <Text style={styles.text}>{alert.description}</Text>
      <Text style={styles.meta}>confidence {alert.confidence.toFixed(2)} · {new Date(alert.at).toLocaleString()}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderLeftWidth: 4,
    backgroundColor: colors.cardSoft,
    padding: 10,
    gap: 6,
  },
  type: {
    color: colors.text,
    fontSize: 12,
    fontWeight: '700',
  },
  text: {
    color: colors.text,
    fontSize: 13,
  },
  meta: {
    color: colors.muted,
    fontSize: 11,
  },
});
