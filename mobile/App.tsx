// File: mobile/App.tsx
import React from 'react'
import { StatusBar } from 'expo-status-bar'
import { NavigationContainer } from '@react-navigation/native'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import { View, ActivityIndicator, StyleSheet } from 'react-native'

import { AuthProvider, useAuth } from './contexts/AuthContext'
import LoginScreen from './screens/auth/LoginScreen'
import RegisterScreen from './screens/auth/RegisterScreen'
import DashboardScreen from './screens/main/DashboardScreen'
import ProfileScreen from './screens/main/ProfileScreen'
import DeviceManagementScreen from './screens/main/DeviceManagementScreen'
import BiometricEnrollmentScreen from './screens/main/BiometricEnrollmentScreen'

// Navigation types
export type AuthStackParamList = {
  Login: undefined
  Register: undefined
}

export type MainStackParamList = {
  Dashboard: undefined
  Profile: undefined
  DeviceManagement: undefined
  BiometricEnrollment: { deviceId?: string }
}

const AuthStack = createNativeStackNavigator<AuthStackParamList>()
const MainStack = createNativeStackNavigator<MainStackParamList>()

// Auth Navigator
const AuthNavigator = () => {
  return (
    <AuthStack.Navigator
      initialRouteName="Login"
      screenOptions={{
        headerShown: false,
        gestureEnabled: true,
      }}
    >
      <AuthStack.Screen name="Login" component={LoginScreen} />
      <AuthStack.Screen name="Register" component={RegisterScreen} />
    </AuthStack.Navigator>
  )
}

// Main App Navigator
const MainNavigator = () => {
  return (
    <MainStack.Navigator
      initialRouteName="Dashboard"
      screenOptions={{
        headerStyle: {
          backgroundColor: '#2563eb',
        },
        headerTintColor: '#ffffff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <MainStack.Screen 
        name="Dashboard" 
        component={DashboardScreen}
        options={{ title: 'Presient Dashboard' }}
      />
      <MainStack.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{ title: 'My Profile' }}
      />
      <MainStack.Screen 
        name="DeviceManagement" 
        component={DeviceManagementScreen}
        options={{ title: 'My Devices' }}
      />
      <MainStack.Screen 
        name="BiometricEnrollment" 
        component={BiometricEnrollmentScreen}
        options={{ title: 'Enroll Biometrics' }}
      />
    </MainStack.Navigator>
  )
}

// Root App Component
const AppContent = () => {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    )
  }

  return (
    <NavigationContainer>
      {user ? <MainNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  )
}

// Main App Export
export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <AppContent />
        <StatusBar style="auto" />
      </AuthProvider>
    </SafeAreaProvider>
  )
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
  },
})