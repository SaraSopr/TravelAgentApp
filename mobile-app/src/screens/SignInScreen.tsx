import { useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { AppContainer } from '@/components/AppContainer';
import { SectionCard } from '@/components/SectionCard';
import { login, register } from '@/services/authService';
import { saveSession } from '@/services/storage';
import { useAuthStore } from '@/store/authStore';
import { colors } from '@/theme/colors';

export function SignInScreen() {
  const [username, setUsername] = useState('sara');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const setSession = useAuthStore((state) => state.setSession);

  const submit = async (mode: 'login' | 'register') => {
    try {
      setLoading(true);
      const payload = mode === 'login' ? await login(username, password) : await register(username, password);
      setSession(payload);
      await saveSession(payload.access_token, payload.refresh_token ?? '', payload.user_id, payload.username);
    } catch (error: any) {
      Alert.alert('Auth error', error?.response?.data?.detail || error?.message || 'Unexpected error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppContainer scroll={false}>
      <View style={styles.hero}>
        <Text style={styles.title}>Travel Agent Mobile</Text>
        <Text style={styles.subtitle}>Realtime itinerary orchestration for dynamic cities</Text>
      </View>

      <SectionCard title="Sign In" subtitle="Access your adaptive travel assistant">
        <TextInput value={username} onChangeText={setUsername} placeholder="Username" placeholderTextColor={colors.muted} style={styles.input} autoCapitalize="none" />
        <TextInput value={password} onChangeText={setPassword} placeholder="Password" placeholderTextColor={colors.muted} style={styles.input} secureTextEntry />

        <Pressable style={styles.primaryButton} onPress={() => submit('login')} disabled={loading}>
          <Text style={styles.primaryText}>{loading ? 'Loading...' : 'Login'}</Text>
        </Pressable>

        <Pressable style={styles.secondaryButton} onPress={() => submit('register')} disabled={loading}>
          <Text style={styles.secondaryText}>Create account</Text>
        </Pressable>
      </SectionCard>
    </AppContainer>
  );
}

const styles = StyleSheet.create({
  hero: {
    marginTop: 30,
    marginBottom: 10,
    gap: 6,
  },
  title: {
    color: colors.white,
    fontSize: 30,
    fontWeight: '800',
  },
  subtitle: {
    color: colors.muted,
    fontSize: 14,
  },
  input: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.cardSoft,
    color: colors.text,
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  primaryButton: {
    marginTop: 4,
    borderRadius: 12,
    backgroundColor: colors.primary,
    alignItems: 'center',
    paddingVertical: 12,
  },
  primaryText: {
    color: colors.white,
    fontWeight: '700',
  },
  secondaryButton: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    paddingVertical: 12,
    backgroundColor: colors.cardSoft,
  },
  secondaryText: {
    color: colors.text,
    fontWeight: '600',
  },
});
