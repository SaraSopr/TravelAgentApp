import { Ionicons } from '@expo/vector-icons';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { HomeScreen } from '@/screens/HomeScreen';
import { NewTripScreen } from '@/screens/NewTripScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { SignInScreen } from '@/screens/SignInScreen';
import { useAuthStore } from '@/store/authStore';
import { colors } from '@/theme/colors';

import { MainTabParamList, RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tabs = createBottomTabNavigator<MainTabParamList>();

function MainTabs() {
  return (
    <Tabs.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.card,
          borderTopColor: colors.border,
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        tabBarIcon: ({ color, size }) => {
          const icon = route.name === 'Home' ? 'compass-outline' : route.name === 'NewTrip' ? 'add-circle-outline' : 'person-outline';
          return <Ionicons name={icon as any} size={size} color={color} />;
        },
      })}
    >
      <Tabs.Screen name="Home" component={HomeScreen} />
      <Tabs.Screen name="NewTrip" component={NewTripScreen} options={{ title: 'Create' }} />
      <Tabs.Screen name="Profile" component={ProfileScreen} />
    </Tabs.Navigator>
  );
}

export function RootNavigator() {
  const accessToken = useAuthStore((state) => state.accessToken);

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {accessToken ? <Stack.Screen name="MainTabs" component={MainTabs} /> : <Stack.Screen name="Auth" component={SignInScreen} />}
    </Stack.Navigator>
  );
}
