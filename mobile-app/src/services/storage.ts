import * as SecureStore from 'expo-secure-store';

const ACCESS_KEY = 'travel_agent_access_token';
const REFRESH_KEY = 'travel_agent_refresh_token';
const USERNAME_KEY = 'travel_agent_username';
const USERID_KEY = 'travel_agent_userid';

export async function saveSession(access: string, refresh: string, userId: string, username: string) {
  await Promise.all([
    SecureStore.setItemAsync(ACCESS_KEY, access),
    SecureStore.setItemAsync(REFRESH_KEY, refresh),
    SecureStore.setItemAsync(USERID_KEY, userId),
    SecureStore.setItemAsync(USERNAME_KEY, username),
  ]);
}

export async function readSession() {
  const [accessToken, refreshToken, userId, username] = await Promise.all([
    SecureStore.getItemAsync(ACCESS_KEY),
    SecureStore.getItemAsync(REFRESH_KEY),
    SecureStore.getItemAsync(USERID_KEY),
    SecureStore.getItemAsync(USERNAME_KEY),
  ]);
  return { accessToken, refreshToken, userId, username };
}

export async function clearSessionStorage() {
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_KEY),
    SecureStore.deleteItemAsync(REFRESH_KEY),
    SecureStore.deleteItemAsync(USERID_KEY),
    SecureStore.deleteItemAsync(USERNAME_KEY),
  ]);
}
