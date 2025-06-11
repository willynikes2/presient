// Minimal App.tsx - Works without context files
import React from 'react'
import { StatusBar } from 'expo-status-bar'
import { NavigationContainer, DefaultTheme } from '@react-navigation/native'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native'

// Auth Context (existing)
import { AuthProvider, useAuth } from './contexts/AuthContext'

// Existing Screens
import HybridLoginScreen from './screens/auth/HybridLoginScreen'
import DashboardScreen from './screens/main/DashboardScreen'
import BiometricEnrollmentScreen from './screens/main/BiometricEnrollmentScreen'

// Inline Notification Test Screen (no context needed)
const NotificationTestScreen = () => {
  const handleTestNotification = async () => {
    try {
      // Simple in-app notification test
      Alert.alert(
        '🔔 Ring-Style Notification Test',
        'testimg2_gnail_cm detected at Mobile Sensor with 99.1% confidence',
        [
          {
            text: 'View Details',
            onPress: () => {
              Alert.alert('Navigation', 'Would navigate to sensor detail screen')
            }
          },
          { text: 'Dismiss' }
        ]
      )
    } catch (error) {
      Alert.alert('Error', 'Notification test failed')
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.emoji}>🔔</Text>
      <Text style={styles.title}>Ring-Style Notifications</Text>
      <Text style={styles.subtitle}>
        Test the notification experience that will integrate with your biometric system
      </Text>
      
      <TouchableOpacity style={styles.button} onPress={handleTestNotification}>
        <Text style={styles.buttonText}>🧪 Test Ring Notification</Text>
      </TouchableOpacity>
      
      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>Expected Integration:</Text>
        <Text style={styles.infoText}>• Authentication → 99.1% confidence</Text>
        <Text style={styles.infoText}>• MQTT → Home Assistant</Text>
        <Text style={styles.infoText}>• Shield automation → ✅ Working</Text>
        <Text style={styles.infoText}>• Push notification → This screen</Text>
      </View>
    </View>
  )
}

// Simple placeholder screens
const WearableSetupScreen = () => (
  <View style={styles.container}>
    <Text style={styles.emoji}>⌚</Text>
    <Text style={styles.title}>Apple Watch Setup</Text>
    <Text style={styles.subtitle}>Coming Soon</Text>
  </View>
)

const SensorDetailScreen = () => {
  const route = require('@react-navigation/native').useRoute()
  const params = route.params || {}
  
  return (
    <View style={styles.container}>
      <Text style={styles.emoji}>📡</Text>
      <Text style={styles.title}>Sensor Detail</Text>
      <Text style={styles.subtitle}>
        Sensor: {params.sensor || 'mobile_app_sensor'}
      </Text>
      <Text style={styles.subtitle}>
        Person: {params.person || 'testimg2_gnail_cm'}
      </Text>
      <Text style={styles.subtitle}>
        Confidence: {params.confidence ? Math.round(params.confidence * 100) + '%' : '99.1%'}
      </Text>
    </View>
  )
}

const AutomationSettingsScreen = () => (
  <View style={styles.container}>
    <Text style={styles.emoji}>⚙️</Text>
    <Text style={styles.title}>Automation Settings</Text>
    <Text style={styles.subtitle}>Decouple Shield automation settings</Text>
  </View>
)

const ProfileScreen = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Profile Screen</Text>
    <Text style={styles.subtitle}>Coming Soon</Text>
  </View>
)

const DeviceManagementScreen = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Device Management</Text>
    <Text style={styles.subtitle}>Coming Soon</Text>
  </View>
)

const FirmwareUpdateScreen = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Firmware Update</Text>
    <Text style={styles.subtitle}>Coming Soon</Text>
  </View>
)

const SensorDiscoveryScreen = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Sensor Discovery</Text>
    <Text style={styles.subtitle}>Coming Soon</Text>
  </View>
)

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    padding: 20,
  },
  emoji: {
    fontSize: 64,
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 22,
  },
  button: {
    backgroundColor: '#3b82f6',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginBottom: 30,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  infoContainer: {
    backgroundColor: '#1e293b',
    padding: 20,
    borderRadius: 12,
    width: '100%',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 6,
  },
})

// Navigation Types
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

// Dark theme
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

// Auth Navigator
const AuthNavigator = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="HybridLogin" component={HybridLoginScreen} />
  </Stack.Navigator>
)

// Main Navigator
const MainNavigator = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#1e293b' },
      headerTintColor: '#ffffff',
      headerTitleStyle: { fontWeight: 'bold' },
    }}
  >
    <Stack.Screen name="Dashboard" component={DashboardScreen} options={{ title: 'Presient' }} />
    <Stack.Screen name="Profile" component={ProfileScreen} options={{ title: 'User Profile' }} />
    <Stack.Screen name="DeviceManagement" component={DeviceManagementScreen} options={{ title: 'Manage Devices' }} />
    <Stack.Screen name="BiometricEnrollment" component={BiometricEnrollmentScreen} options={{ title: 'Enroll Biometrics' }} />
    <Stack.Screen name="WearableSetup" component={WearableSetupScreen} options={{ title: 'Apple Watch Setup' }} />
    <Stack.Screen name="SensorDetail" component={SensorDetailScreen} options={{ title: 'Sensor Activity' }} />
    <Stack.Screen name="AutomationSettings" component={AutomationSettingsScreen} options={{ title: 'Automation Settings' }} />
    <Stack.Screen name="NotificationTest" component={NotificationTestScreen} options={{ title: 'Test Notifications' }} />
    <Stack.Screen name="FirmwareUpdate" component={FirmwareUpdateScreen} options={{ title: 'Firmware Update' }} />
    <Stack.Screen name="SensorDiscovery" component={SensorDiscoveryScreen} options={{ title: 'Discover Sensors' }} />
  </Stack.Navigator>
)

// Loading Component
const LoadingScreen = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Loading...</Text>
  </View>
)

// App Content
const AppContent = () => {
  const { user, loading } = useAuth()
  if (loading) return <LoadingScreen />
  return (
    <NavigationContainer theme={DarkTheme}>
      {user ? <MainNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  )
}

// Main App Component (no context imports - they don't exist yet)
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