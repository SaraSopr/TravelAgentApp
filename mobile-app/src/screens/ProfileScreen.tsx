import { useEffect, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, View } from 'react-native';

import { AppContainer } from '@/components/AppContainer';
import { SectionCard } from '@/components/SectionCard';
import { logout } from '@/services/authService';
import { clearSessionStorage, readSession } from '@/services/storage';
import { useAuthStore } from '@/store/authStore';
import { colors } from '@/theme/colors';

export function ProfileScreen() {
  const { username, refreshToken, clearSession, markHydrated, setSession } = useAuthStore();
  const [sessionInfo, setSessionInfo] = useState('');

  useEffect(() => {
    (async () => {
      const session = await readSession();
      if (session.accessToken && session.userId && session.username) {
        setSession({
          access_token: session.accessToken,
          refresh_token: session.refreshToken || '',
          token_type: 'bearer',
          user_id: session.userId,
          username: session.username,
        });
      } else {
        markHydrated();
      }
      setSessionInfo(`Persisted token: ${session.accessToken ? 'yes' : 'no'}`);
    })();
  }, [markHydrated, setSession]);

  const doLogout = async () => {
    try {
      if (refreshToken) {
        await logout(refreshToken);
      }
    } catch {
    } finally {
      await clearSessionStorage();
      clearSession();
      Alert.alert('Logged out', 'Your session has been revoked.');
    }
  };

  return (
    <AppContainer>
      <SectionCard title="Profile" subtitle="Security & session controls">
        <Text style={styles.label}>User</Text>
        <Text style={styles.value}>{username || 'Not authenticated'}</Text>

        <Text style={styles.label}>Session</Text>
        <Text style={styles.value}>{sessionInfo}</Text>

        <Pressable onPress={doLogout} style={styles.button}>
          <Text style={styles.buttonText}>Logout & revoke tokens</Text>
        </Pressable>
      </SectionCard>
    </AppContainer>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontSize: 12,
    marginTop: 6,
  },
  value: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '600',
  },
  button: {
    marginTop: 10,
    borderRadius: 12,
    backgroundColor: colors.danger,
    alignItems: 'center',
    paddingVertical: 12,
  },
  buttonText: {
    color: colors.white,
    fontWeight: '700',
  },
});
