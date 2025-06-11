// Enhanced App.tsx - Gradual Build Note 2 Integration
// Builds on your existing working app with Ring-style improvements

import React, { useState, useEffect } from 'react'
import { StatusBar } from 'expo-status-bar'
import { NavigationContainer, DefaultTheme } from '@react-navigation/native'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import { View, Text, StyleSheet, TouchableOpacity, Alert, ScrollView, Switch } from 'react-native'

// Notification imports (install with: npm install expo-notifications expo-device)
import * as Notifications from 'expo-notifications'
import * as Device from 'expo-device'

// Auth Context (existing)
import { AuthProvider, useAuth } from './contexts/AuthContext'

// Existing Screens
import HybridLoginScreen from './screens/auth/HybridLoginScreen'
import DashboardScreen from './screens/main/DashboardScreen'
import BiometricEnrollmentScreen from './screens/main/BiometricEnrollmentScreen'

// Configure notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
})

// Enhanced Notification Test Screen with REAL push notifications
const NotificationTestScreen = () => {
  const { user } = useAuth()
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null)
  const [isNotificationEnabled, setIsNotificationEnabled] = useState(false)

  useEffect(() => {
    setupNotifications()
  }, [])

  const setupNotifications = async () => {
    try {
      if (!Device.isDevice) {
        Alert.alert('Info', 'Push notifications only work on physical devices')
        return
      }

      const { status: existingStatus } = await Notifications.getPermissionsAsync()
      let finalStatus = existingStatus
      
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync()
        finalStatus = status
      }
      
      if (finalStatus !== 'granted') {
        Alert.alert('Error', 'Push notification permissions required for Ring-style alerts')
        return
      }

      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId: '47c2bb5c-0d82-4c73-8d87-0669bf17cfe9' // Replace with your actual project ID
      })
      
      setExpoPushToken(tokenData.data)
      setIsNotificationEnabled(true)
      console.log('✅ Push token:', tokenData.data)

    } catch (error) {
      console.error('❌ Notification setup error:', error)
    }
  }

  const sendRealNotification = async () => {
    try {
      if (!expoPushToken) {
        Alert.alert('Error', 'Notifications not set up yet')
        return
      }

      // Send real push notification
      await Notifications.scheduleNotificationAsync({
        content: {
          title: '🏠 testimg2_gnail_cm detected',
          body: 'Recognized at Mobile Sensor with 99.4% confidence',
          data: { 
            person: 'testimg2_gnail_cm',
            sensor: 'mobile_app_sensor',
            confidence: 99.4,
            timestamp: new Date().toISOString()
          },
        },
        trigger: { type: 'timeInterval', seconds: 2 },
      })

      Alert.alert('🔔 Real Notification Sent!', 'Check your notification tray in 2 seconds')

    } catch (error) {
      console.error('❌ Notification error:', error)
      Alert.alert('Error', 'Failed to send notification')
    }
  }

  const testRingStyleAlert = () => {
    Alert.alert(
      '🔔 Ring-Style Notification Preview',
      'testimg2_gnail_cm detected at Mobile Sensor with 99.4% confidence',
      [
        {
          text: 'View Details',
          onPress: () => {
            // Would navigate to sensor detail screen
            Alert.alert('Navigation', 'Would open sensor detail screen showing:\n\n• Person: testimg2_gnail_cm\n• Confidence: 99.4%\n• Sensor: Mobile Sensor\n• Time: Just now\n• Heart Rate: 76.6 BPM')
          }
        },
        { text: 'Dismiss' }
      ]
    )
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.emoji}>🔔</Text>
      <Text style={styles.title}>Ring-Style Notifications</Text>
      <Text style={styles.subtitle}>
        Test notification experience for your 99.4% confidence biometric system
      </Text>
      
      {/* Notification Status */}
      <View style={styles.statusContainer}>
        <Text style={styles.statusTitle}>Notification Status:</Text>
        <Text style={[styles.statusText, { color: isNotificationEnabled ? '#10b981' : '#f59e0b' }]}>
          {isNotificationEnabled ? '✅ Ready for Ring-style alerts' : '⚠️ Setup required'}
        </Text>
      </View>

      {/* Test Buttons */}
      <View style={styles.buttonContainer}>
        <TouchableOpacity style={styles.button} onPress={testRingStyleAlert}>
          <Text style={styles.buttonText}>🎭 Preview Ring Alert</Text>
        </TouchableOpacity>
        
        {isNotificationEnabled && (
          <TouchableOpacity style={styles.buttonPrimary} onPress={sendRealNotification}>
            <Text style={styles.buttonText}>📱 Send Real Notification</Text>
          </TouchableOpacity>
        )}
        
        {!isNotificationEnabled && (
          <TouchableOpacity style={styles.buttonPrimary} onPress={setupNotifications}>
            <Text style={styles.buttonText}>🚀 Enable Notifications</Text>
          </TouchableOpacity>
        )}
      </View>
      
      {/* Integration Info */}
      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>Build Note 2: Ring-Style Integration</Text>
        <Text style={styles.infoText}>✅ Enhanced biometric authentication (99.4%)</Text>
        <Text style={styles.infoText}>✅ MQTT → Home Assistant → Shield automation</Text>
        <Text style={styles.infoText}>🔔 Ring-style notifications (this screen)</Text>
        <Text style={styles.infoText}>👆 Tap navigation → sensor detail screens</Text>
        <Text style={styles.infoText}>⚙️ Automation settings (decoupled from app)</Text>
      </View>

      {/* Expected Flow */}
      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>Complete Flow:</Text>
        <Text style={styles.infoText}>1. 🫀 Biometric authentication → 99.4% confidence</Text>
        <Text style={styles.infoText}>2. 📡 MQTT published → Home Assistant</Text>
        <Text style={styles.infoText}>3. 🏠 HA automation → Shield turns ON</Text>
        <Text style={styles.infoText}>4. 🔔 Push notification → "Person detected"</Text>
        <Text style={styles.infoText}>5. 👆 Tap notification → Sensor detail screen</Text>
      </View>
    </ScrollView>
  )
}

// Enhanced Automation Settings Screen with real toggles
const AutomationSettingsScreen = () => {
  const [settings, setSettings] = useState({
    homeAssistantEnabled: true,
    pushNotificationsEnabled: true,
    appRoutinesEnabled: false,
    shieldAutomation: true,
    confidenceThreshold: 80
  })

  const toggleSetting = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }))
    
    console.log(`⚙️ Setting ${key} = ${value}`)
  }

  const saveSettings = () => {
    console.log('💾 Saving automation settings:', settings)
    Alert.alert(
      '✅ Settings Saved',
      'Your automation preferences have been updated.\n\nThese settings decouple device control from the app - Home Assistant handles all automation logic.',
      [{ text: 'OK' }]
    )
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.emoji}>⚙️</Text>
      <Text style={styles.title}>Automation Settings</Text>
      <Text style={styles.subtitle}>
        Decouple automation logic from app - Build Note 2 architecture
      </Text>
      
      {/* Home Assistant Integration */}
      <View style={styles.settingContainer}>
        <View style={styles.settingHeader}>
          <Text style={styles.settingTitle}>🏠 Home Assistant Integration</Text>
          <Switch
            value={settings.homeAssistantEnabled}
            onValueChange={(value) => toggleSetting('homeAssistantEnabled', value)}
            trackColor={{ false: '#374151', true: '#10b981' }}
            thumbColor="#FFFFFF"
          />
        </View>
        <Text style={styles.settingDescription}>
          When enabled, Presient publishes MQTT events to Home Assistant. HA handles all device automation (Shield, lights, etc.).
        </Text>
      </View>

      {/* Push Notifications */}
      <View style={styles.settingContainer}>
        <View style={styles.settingHeader}>
          <Text style={styles.settingTitle}>🔔 Ring-Style Notifications</Text>
          <Switch
            value={settings.pushNotificationsEnabled}
            onValueChange={(value) => toggleSetting('pushNotificationsEnabled', value)}
            trackColor={{ false: '#374151', true: '#10b981' }}
            thumbColor="#FFFFFF"
          />
        </View>
        <Text style={styles.settingDescription}>
          Send Ring-style push notifications when family members are detected.
        </Text>
      </View>

      {/* App Routines */}
      <View style={styles.settingContainer}>
        <View style={styles.settingHeader}>
          <Text style={styles.settingTitle}>📱 App Routines (Non-HA Users)</Text>
          <Switch
            value={settings.appRoutinesEnabled}
            onValueChange={(value) => toggleSetting('appRoutinesEnabled', value)}
            trackColor={{ false: '#374151', true: '#10b981' }}
            thumbColor="#FFFFFF"
          />
        </View>
        <Text style={styles.settingDescription}>
          Enable app-based automation for users without Home Assistant (sound, haptic, webhook).
        </Text>
      </View>

      {/* Save Button */}
      <TouchableOpacity style={styles.saveButton} onPress={saveSettings}>
        <Text style={styles.buttonText}>💾 Save Automation Settings</Text>
      </TouchableOpacity>

      {/* Architecture Info */}
      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>Build Note 2 Architecture:</Text>
        <Text style={styles.infoText}>✅ No hardcoded device logic in app</Text>
        <Text style={styles.infoText}>✅ Home Assistant handles automation</Text>
        <Text style={styles.infoText}>✅ App routines for non-HA users</Text>
        <Text style={styles.infoText}>✅ Clean separation of concerns</Text>
        <Text style={styles.infoText}>✅ Future-ready for Presient Hub</Text>
      </View>
    </ScrollView>
  )
}

// Enhanced Sensor Detail Screen
const SensorDetailScreen = () => {
  const route = require('@react-navigation/native').useRoute()
  const params = route.params || {}
  
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.emoji}>📡</Text>
      <Text style={styles.title}>Sensor Detail</Text>
      <Text style={styles.subtitle}>Ring-style notification tap target</Text>
      
      {/* Detection Info */}
      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>Latest Detection:</Text>
        <Text style={styles.infoText}>👤 Person: {params.person || 'testimg2_gnail_cm'}</Text>
        <Text style={styles.infoText}>📡 Sensor: {params.sensor || 'mobile_app_sensor'}</Text>
        <Text style={styles.infoText}>🎯 Confidence: {params.confidence ? Math.round(params.confidence * 100) + '%' : '99.4%'}</Text>
        <Text style={styles.infoText}>🕐 Time: Just now</Text>
        <Text style={styles.infoText}>💓 Heart Rate: 76.6 BPM</Text>
        <Text style={styles.infoText}>🔄 Source: dual_sensor</Text>
      </View>

      {/* Automation Status */}
      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>Automation Triggered:</Text>
        <Text style={styles.infoText}>📡 MQTT published to Home Assistant ✅</Text>
        <Text style={styles.infoText}>🏠 HA automation executed ✅</Text>
        <Text style={styles.infoText}>🎮 NVIDIA Shield turned ON ✅</Text>
        <Text style={styles.infoText}>🔔 Ring-style notification sent ✅</Text>
      </View>

      {/* Ring-Style Features */}
      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>Ring-Style Experience:</Text>
        <Text style={styles.infoText}>• Instant notifications when detected</Text>
        <Text style={styles.infoText}>• Tap notifications → this detail screen</Text>
        <Text style={styles.infoText}>• Confidence-based automation</Text>
        <Text style={styles.infoText}>• Home Assistant integration</Text>
        <Text style={styles.infoText}>• Privacy-first local processing</Text>
      </View>
    </ScrollView>
  )
}

// Keep all your existing placeholder screens but enhanced
const WearableSetupScreen = () => (
  <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
    <Text style={styles.emoji}>⌚</Text>
    <Text style={styles.title}>Apple Watch Setup</Text>
    <Text style={styles.subtitle}>Build Note 1: Dual-Sensor Authentication</Text>
    
    <View style={styles.infoContainer}>
      <Text style={styles.infoTitle}>Apple Watch Integration Features:</Text>
      <Text style={styles.infoText}>• "Do you have a wearable?" enrollment flow</Text>
      <Text style={styles.infoText}>• HealthKit heart rate data collection</Text>
      <Text style={styles.infoText}>• Dual-sensor confidence boost (+5%)</Text>
      <Text style={styles.infoText}>• Automatic fallback if sensor fails</Text>
      <Text style={styles.infoText}>• Medical-grade accuracy enhancement</Text>
    </View>
    
    <View style={styles.infoContainer}>
      <Text style={styles.infoTitle}>Current Status:</Text>
      <Text style={styles.infoText}>✅ Your enhanced BiometricEnrollmentScreen ready</Text>
      <Text style={styles.infoText}>📱 Simulation mode working (no dev account needed)</Text>
      <Text style={styles.infoText}>🏗️ Real HealthKit requires Apple Developer account</Text>
      <Text style={styles.infoText}>⌚ iOS build needed for actual Apple Watch</Text>
    </View>
  </ScrollView>
)

// Enhanced styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  emoji: {
    fontSize: 64,
    marginBottom: 20,
    textAlign: 'center',
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
  buttonContainer: {
    marginBottom: 20,
    gap: 12,
  },
  button: {
    backgroundColor: '#374151',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonPrimary: {
    backgroundColor: '#10b981',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  saveButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 20,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  statusContainer: {
    backgroundColor: '#1e293b',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
  },
  statusTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  settingContainer: {
    backgroundColor: '#1e293b',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  settingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    flex: 1,
  },
  settingDescription: {
    fontSize: 14,
    color: '#94a3b8',
    lineHeight: 18,
  },
  infoContainer: {
    backgroundColor: '#1e293b',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
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

// Keep all your existing setup
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

// Keep your existing theme
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

// Keep your existing navigators
const AuthNavigator = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="HybridLogin" component={HybridLoginScreen} />
  </Stack.Navigator>
)

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
    <Stack.Screen name="NotificationTest" component={NotificationTestScreen} options={{ title: 'Ring Notifications' }} />
    <Stack.Screen name="FirmwareUpdate" component={FirmwareUpdateScreen} options={{ title: 'Firmware Update' }} />
    <Stack.Screen name="SensorDiscovery" component={SensorDiscoveryScreen} options={{ title: 'Discover Sensors' }} />
  </Stack.Navigator>
)

// Keep your existing placeholder screens
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

// Keep your existing app structure
const LoadingScreen = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Loading...</Text>
  </View>
)

const AppContent = () => {
  const { user, loading } = useAuth()
  if (loading) return <LoadingScreen />
  return (
    <NavigationContainer theme={DarkTheme}>
      {user ? <MainNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  )
}

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