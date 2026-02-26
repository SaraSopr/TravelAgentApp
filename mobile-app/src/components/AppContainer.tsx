import { PropsWithChildren } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { colors } from '@/theme/colors';

type Props = PropsWithChildren<{
  scroll?: boolean;
}>;

export function AppContainer({ children, scroll = true }: Props) {
  const content = scroll ? (
    <ScrollView contentContainerStyle={styles.content}>{children}</ScrollView>
  ) : (
    <View style={styles.content}>{children}</View>
  );

  return (
    <LinearGradient colors={[colors.bg, '#0F1A2D']} style={styles.root}>
      {content}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: {
    padding: 16,
    gap: 14,
    paddingBottom: 32,
  },
});
