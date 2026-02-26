import { createNavigationContainerRef } from '@react-navigation/native';

export const navigationRef = createNavigationContainerRef<any>();

export function openHomeFromNotification() {
  if (!navigationRef.isReady()) {
    return;
  }
  navigationRef.navigate('MainTabs', { screen: 'Home' });
}
