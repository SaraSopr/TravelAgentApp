import 'react-native-gesture-handler';
import { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import * as Notifications from 'expo-notifications';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { navigationRef, openHomeFromNotification } from './src/navigation/navigationRef';
import { RootNavigator } from './src/navigation/RootNavigator';
import { initializeNotifications } from './src/services/notifications';
import { useUiStore } from './src/store/uiStore';

export default function App() {
  const setPendingTripIdFromNotification = useUiStore((state) => state.setPendingTripIdFromNotification);

  useEffect(() => {
    initializeNotifications();

    const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data as { tripId?: string } | undefined;
      if (data?.tripId) {
        setPendingTripIdFromNotification(String(data.tripId));
      }
      openHomeFromNotification();
    });

    return () => {
      subscription.remove();
    };
  }, []);

  return (
    <SafeAreaProvider>
      <NavigationContainer ref={navigationRef}>
        <StatusBar style="light" />
        <RootNavigator />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
