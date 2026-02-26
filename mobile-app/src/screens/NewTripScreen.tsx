import { useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { AppContainer } from '@/components/AppContainer';
import { SectionCard } from '@/components/SectionCard';
import { createTrip } from '@/services/tripService';
import { colors } from '@/theme/colors';

const nowPlusOneHour = new Date(Date.now() + 60 * 60 * 1000).toISOString();

export function NewTripScreen() {
  const [city, setCity] = useState('Milan');
  const [intent, setIntent] = useState('Cultura al mattino, passeggiata pomeriggio e cena in area sicura.');
  const [startAt, setStartAt] = useState(nowPlusOneHour);
  const [interests, setInterests] = useState('culture, food, sightseeing');
  const [budget, setBudget] = useState<'low' | 'medium' | 'high'>('medium');
  const [mobility, setMobility] = useState<'walk' | 'public_transport' | 'taxi'>('public_transport');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    try {
      setLoading(true);
      const correlation = await createTrip({
        city,
        intent,
        start_time: startAt,
        budget_level: budget,
        mobility_mode: mobility,
        interests: interests.split(',').map((v) => v.trim()).filter(Boolean),
      });
      Alert.alert('Trip created', `Correlation: ${correlation.correlation_id}`);
    } catch (error: any) {
      Alert.alert('Create trip failed', error?.response?.data?.detail || error?.message || 'Unexpected error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppContainer>
      <SectionCard title="Create Smart Trip" subtitle="Generate a resilient itinerary ready for disruptions">
        <TextInput value={city} onChangeText={setCity} style={styles.input} placeholder="City" placeholderTextColor={colors.muted} />
        <TextInput value={intent} onChangeText={setIntent} multiline style={[styles.input, styles.textArea]} placeholder="Intent" placeholderTextColor={colors.muted} />
        <TextInput value={startAt} onChangeText={setStartAt} style={styles.input} placeholder="Start ISO datetime" placeholderTextColor={colors.muted} />
        <TextInput value={interests} onChangeText={setInterests} style={styles.input} placeholder="culture, food" placeholderTextColor={colors.muted} />

        <View style={styles.row}>
          <Pressable onPress={() => setBudget('low')} style={[styles.chip, budget === 'low' && styles.chipActive]}><Text style={styles.chipText}>Low</Text></Pressable>
          <Pressable onPress={() => setBudget('medium')} style={[styles.chip, budget === 'medium' && styles.chipActive]}><Text style={styles.chipText}>Medium</Text></Pressable>
          <Pressable onPress={() => setBudget('high')} style={[styles.chip, budget === 'high' && styles.chipActive]}><Text style={styles.chipText}>High</Text></Pressable>
        </View>

        <View style={styles.row}>
          <Pressable onPress={() => setMobility('walk')} style={[styles.chip, mobility === 'walk' && styles.chipActive]}><Text style={styles.chipText}>Walk</Text></Pressable>
          <Pressable onPress={() => setMobility('public_transport')} style={[styles.chip, mobility === 'public_transport' && styles.chipActive]}><Text style={styles.chipText}>Public</Text></Pressable>
          <Pressable onPress={() => setMobility('taxi')} style={[styles.chip, mobility === 'taxi' && styles.chipActive]}><Text style={styles.chipText}>Taxi</Text></Pressable>
        </View>

        <Pressable style={styles.submit} onPress={submit} disabled={loading}>
          <Text style={styles.submitText}>{loading ? 'Submitting...' : 'Create Itinerary'}</Text>
        </Pressable>
      </SectionCard>
    </AppContainer>
  );
}

const styles = StyleSheet.create({
  input: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.cardSoft,
    color: colors.text,
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  textArea: {
    minHeight: 88,
    textAlignVertical: 'top',
  },
  row: {
    flexDirection: 'row',
    gap: 8,
  },
  chip: {
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: colors.cardSoft,
  },
  chipActive: {
    borderColor: colors.primary,
  },
  chipText: {
    color: colors.text,
    fontWeight: '600',
  },
  submit: {
    borderRadius: 12,
    backgroundColor: colors.primary,
    alignItems: 'center',
    paddingVertical: 12,
  },
  submitText: {
    color: colors.white,
    fontWeight: '700',
  },
});
