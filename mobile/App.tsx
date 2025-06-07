// Enhanced App.tsx - Ring-Style Notifications + Apple Watch Integration
import React from 'react'
import { StatusBar } from 'expo-status-bar'
import { NavigationContainer, DefaultTheme } from '@react-navigation/native'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { SafeAreaProvider } from 'react-native-safe-area-context'

// Auth Context
import { AuthProvider, useAuth } from './contexts/AuthContext'

// New Contexts for Ring-Style Features
import { NotificationProvider } from './contexts/NotificationContext'
import { WearableProvider } from './contexts/WearableContext'

// Screens
import HybridLoginScreen from './screens/auth/HybridLoginScreen'
import DashboardScreen from './screens/main/DashboardScreen'
import BiometricEnrollmentScreen from './screens/main/BiometricEnrollmentScreen'

// New Screens for Ring-Style Features
import WearableSetupScreen from './screens/main/WearableSetupScreen'
import SensorDetailScreen from './screens/main/SensorDetailScreen'
import AutomationSettingsScreen from './screens/main/AutomationSettingsScreen'
import NotificationTestScreen from './screens/main/NotificationTestScreen'

// Simple placeholder screens (for buttons that aren't implemented yet)
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

// Enhanced Navigation Types
export type RootStackParamList = {
  HybridLogin: undefined
  Dashboard: undefined
  Profile: undefined
  DeviceManagement: undefined
  BiometricEnrollment: undefined
  WearableSetup: undefined
  SensorDetail: { sensor: string; person?: string; confidence?: number }
  AutomationSettings: undefined
  NotificationTest: undefined
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

// Auth Navigator (Hybrid Login - Social + Email/Password)
const AuthNavigator = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: false,
    }}
  >
    <Stack.Screen name="HybridLogin" component={HybridLoginScreen} />
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
      name="WearableSetup" 
      component={WearableSetupScreen}
      options={{ title: 'Apple Watch Setup' }}
    />
    <Stack.Screen 
      name="SensorDetail" 
      component={SensorDetailScreen}
      options={{ title: 'Sensor Activity' }}
    />
    <Stack.Screen 
      name="AutomationSettings" 
      component={AutomationSettingsScreen}
      options={{ title: 'Automation Settings' }}
    />
    <Stack.Screen 
      name="NotificationTest" 
      component={NotificationTestScreen}
      options={{ title: 'Test Notifications' }}
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

// Root App Component with Enhanced Context Providers
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

// Main App Component with Ring-Style Providers
export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <NotificationProvider>
          <WearableProvider>
            <AppContent />
            <StatusBar style="light" />
          </WearableProvider>
        </NotificationProvider>
      </AuthProvider>
    </SafeAreaProvider>
  )
}