// Fixed App.tsx - Proper Component Exports
import React from 'react'
import { StatusBar } from 'expo-status-bar'
import { NavigationContainer, DefaultTheme } from '@react-navigation/native'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { SafeAreaProvider } from 'react-native-safe-area-context'

// Auth Context
import { AuthProvider, useAuth } from './contexts/AuthContext'

// Screens
import SocialLoginScreen from './screens/auth/SocialLoginScreen'
import DashboardScreen from './screens/main/DashboardScreen'

// Simple placeholder screens (to fix navigation errors)
const ProfileScreen = () => {
  const { View, Text, StyleSheet } = require('react-native')
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Profile Screen</Text>
      <Text style={styles.subtitle}>Coming Soon</Text>
    </View>
  )
}

const DeviceManagementScreen = () => {
  const { View, Text, StyleSheet } = require('react-native')
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Device Management</Text>
      <Text style={styles.subtitle}>Coming Soon</Text>
    </View>
  )
}

const BiometricEnrollmentScreen = () => {
  const { View, Text, StyleSheet } = require('react-native')
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Biometric Enrollment</Text>
      <Text style={styles.subtitle}>Coming Soon</Text>
    </View>
  )
}

const FirmwareUpdateScreen = () => {
  const { View, Text, StyleSheet } = require('react-native')
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Firmware Update</Text>
      <Text style={styles.subtitle}>Coming Soon</Text>
    </View>
  )
}

const SensorDiscoveryScreen = () => {
  const { View, Text, StyleSheet } = require('react-native')
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Sensor Discovery</Text>
      <Text style={styles.subtitle}>Coming Soon</Text>
    </View>
  )
}

// Styles for placeholder screens
const styles = require('react-native').StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
  },
})

// Navigation Types
export type RootStackParamList = {
  SocialLogin: undefined
  Dashboard: undefined
  Profile: undefined
  DeviceManagement: undefined
  BiometricEnrollment: undefined
  FirmwareUpdate: undefined
  SensorDiscovery: undefined
}

const Stack = createNativeStackNavigator<RootStackParamList>()

// Dark theme for navigation
const DarkTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#3b82f6',
    background: '#0f172a',
    card: '#1e293b',
    text: '#ffffff',
    border: '#334155',
    notification: '#3b82f6',
  },
}

// Auth Navigator (Social Login)
const AuthNavigator = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: false,
    }}
  >
    <Stack.Screen name="SocialLogin" component={SocialLoginScreen} />
  </Stack.Navigator>
)

// Main Navigator (Dashboard and other screens)
const MainNavigator = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: {
        backgroundColor: '#1e293b',
      },
      headerTintColor: '#ffffff',
      headerTitleStyle: {
        fontWeight: 'bold',
      },
    }}
  >
    <Stack.Screen 
      name="Dashboard" 
      component={DashboardScreen}
      options={{ title: 'Presient' }}
    />
    <Stack.Screen 
      name="Profile" 
      component={ProfileScreen}
      options={{ title: 'User Profile' }}
    />
    <Stack.Screen 
      name="DeviceManagement" 
      component={DeviceManagementScreen}
      options={{ title: 'Manage Devices' }}
    />
    <Stack.Screen 
      name="BiometricEnrollment" 
      component={BiometricEnrollmentScreen}
      options={{ title: 'Enroll Biometrics' }}
    />
    <Stack.Screen 
      name="FirmwareUpdate" 
      component={FirmwareUpdateScreen}
      options={{ title: 'Firmware Update' }}
    />
    <Stack.Screen 
      name="SensorDiscovery" 
      component={SensorDiscoveryScreen}
      options={{ title: 'Discover Sensors' }}
    />
  </Stack.Navigator>
)

// Loading Component
const LoadingScreen = () => {
  const { View, Text, ActivityIndicator, StyleSheet } = require('react-native')
  return (
    <View style={loadingStyles.container}>
      <ActivityIndicator size="large" color="#3b82f6" />
      <Text style={loadingStyles.text}>Loading...</Text>
    </View>
  )
}

const loadingStyles = require('react-native').StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
  },
  text: {
    marginTop: 16,
    fontSize: 16,
    color: '#64748b',
  },
})

// Root App Component
const AppContent = () => {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingScreen />
  }

  return (
    <NavigationContainer theme={DarkTheme}>
      {user ? <MainNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  )
}

// Main App Component
export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <AppContent />
        <StatusBar style="light" />
      </AuthProvider>
    </SafeAreaProvider>
  )
}