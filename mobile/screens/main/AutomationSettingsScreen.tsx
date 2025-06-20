// Automation Settings Screen - Build Note 2
// mobile/screens/main/AutomationSettingsScreen.tsx

import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Switch,
  Alert,
  ActivityIndicator
} from 'react-native'
import { useNavigation } from '@react-navigation/native'
import { useAuth } from '../../contexts/AuthContext'
import { useNotifications } from '../../contexts/NotificationContext'

interface AutomationSettings {
  homeAssistantEnabled: boolean
  pushNotificationsEnabled: boolean
  appRoutinesEnabled: boolean
  selectedRoutine: string
  soundEnabled: boolean
  hapticEnabled: boolean
  webhookUrl?: string
}

interface AppRoutine {
  id: string
  name: string
  description: string
  actions: string[]
}

const AutomationSettingsScreen = () => {
  const navigation = useNavigation()
  const { user } = useAuth()
  const { isNotificationEnabled, setupNotifications, sendTestNotification } = useNotifications()
  
  const [settings, setSettings] = useState<AutomationSettings>({
    homeAssistantEnabled: true,
    pushNotificationsEnabled: true,
    appRoutinesEnabled: false,
    selectedRoutine: 'notify_only',
    soundEnabled: true,
    hapticEnabled: true
  })
  
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Available app routines for non-HA users
  const appRoutines: AppRoutine[] = [
    {
      id: 'notify_only',
      name: '📱 Notification Only',
      description: 'Send push notification when person detected',
      actions: ['Push notification']
    },
    {
      id: 'notify_sound',
      name: '🔔 Notification + Sound',
      description: 'Send notification and play sound on phone',
      actions: ['Push notification', 'Play sound']
    },
    {
      id: 'notify_haptic',
      name: '📳 Notification + Haptic',
      description: 'Send notification with haptic feedback',
      actions: ['Push notification', 'Haptic feedback']
    },
    {
      id: 'full_routine',
      name: '🎯 Full App Routine',
      description: 'Notification, sound, and haptic feedback',
      actions: ['Push notification', 'Play sound', 'Haptic feedback']
    },
    {
      id: 'webhook_custom',
      name: '🌐 Custom Webhook',
      description: 'Send to custom webhook URL for advanced automation',
      actions: ['Push notification', 'Custom webhook']
    }
  ]

  // Load settings on mount
  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setIsLoading(true)
      console.log('⚙️ Loading automation settings...')
      
      // TODO: Load from AsyncStorage or backend
      // For now, use defaults
      console.log('✅ Settings loaded (using defaults)')
      
    } catch (error) {
      console.error('❌ Error loading settings:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const saveSettings = async () => {
    try {
      setIsSaving(true)
      console.log('💾 Saving automation settings:', settings)
      
      // Save to backend
      const response = await fetch('https://orange-za-speech-dosage.trycloudflare.com/api/automation/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.email?.replace(/[@.]/g, '_') || 'unknown_user',
          settings: settings
        })
      })

      if (response.ok) {
        console.log('✅ Settings saved successfully')
        Alert.alert(
          '✅ Settings Saved',
          'Your automation preferences have been updated.',
          [{ text: 'OK' }],
          { userInterfaceStyle: 'dark' }
        )
      } else {
        throw new Error('Failed to save settings')
      }
      
    } catch (error) {
      console.error('❌ Error saving settings:', error)
      Alert.alert(
        '❌ Save Failed', 
        'Could not save settings. Please try again.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
    } finally {
      setIsSaving(false)
    }
  }

  const toggleHomeAssistant = (enabled: boolean) => {
    setSettings(prev => ({
      ...prev,
      homeAssistantEnabled: enabled,
      appRoutinesEnabled: !enabled // Disable app routines when HA is enabled
    }))
    
    if (enabled) {
      Alert.alert(
        '🏠 Home Assistant Mode',
        'Home Assistant will handle all device automation. App routines will be disabled.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
    }
  }

  const toggleAppRoutines = (enabled: boolean) => {
    if (enabled && settings.homeAssistantEnabled) {
      Alert.alert(
        '⚠️ Conflict',
        'Please disable Home Assistant integration first to use app routines.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
      return
    }
    
    setSettings(prev => ({
      ...prev,
      appRoutinesEnabled: enabled,
      homeAssistantEnabled: !enabled // Disable HA when app routines are enabled
    }))
  }

  const toggleNotifications = async (enabled: boolean) => {
    if (enabled && !isNotificationEnabled) {
      const success = await setupNotifications()
      if (!success) return
    }
    
    setSettings(prev => ({
      ...prev,
      pushNotificationsEnabled: enabled
    }))
  }

  const selectRoutine = (routineId: string) => {
    setSettings(prev => ({
      ...prev,
      selectedRoutine: routineId
    }))
  }

  const testCurrentSetup = async () => {
    try {
      console.log('🧪 Testing current automation setup...')
      
      if (settings.pushNotificationsEnabled) {
        await sendTestNotification()
      }
      
      if (settings.appRoutinesEnabled) {
        const routine = appRoutines.find(r => r.id === settings.selectedRoutine)
        Alert.alert(
          '🧪 App Routine Test',
          `Testing "${routine?.name}" routine:\n\n${routine?.actions.join('\n')}`,
          [{ text: 'OK' }],
          { userInterfaceStyle: 'dark' }
        )
      }
      
      if (settings.homeAssistantEnabled) {
        Alert.alert(
          '🏠 Home Assistant Test',
          'MQTT presence event would be published to Home Assistant for automation.',
          [{ text: 'OK' }],
          { userInterfaceStyle: 'dark' }
        )
      }
      
    } catch (error) {
      console.error('❌ Test error:', error)
    }
  }

  const getSelectedRoutine = () => {
    return appRoutines.find(r => r.id === settings.selectedRoutine)
  }

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#10B981" />
          <Text style={styles.loadingText}>Loading automation settings...</Text>
        </View>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>⚙️ Automation Settings</Text>
          <Text style={styles.subtitle}>
            Configure how Presient handles presence detection events
          </Text>
        </View>

        {/* Home Assistant Integration */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>🏠 Home Assistant Integration</Text>
            <Switch
              value={settings.homeAssistantEnabled}
              onValueChange={toggleHomeAssistant}
              trackColor={{ false: '#374151', true: '#10B981' }}
              thumbColor="#FFFFFF"
            />
          </View>
          <Text style={styles.sectionDescription}>
            When enabled, Presient publishes MQTT events to Home Assistant for smart home automation. 
            Disable this to use app-based routines instead.
          </Text>
          {settings.homeAssistantEnabled && (
            <View style={styles.statusContainer}>
              <Text style={styles.statusText}>✅ MQTT events published to Home Assistant</Text>
              <Text style={styles.statusText}>🏠 Home Assistant handles all device control</Text>
              <Text style={styles.statusText}>📡 Topic: presient/presence</Text>
            </View>
          )}
        </View>

        {/* Push Notifications */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>🔔 Push Notifications</Text>
            <Switch
              value={settings.pushNotificationsEnabled}
              onValueChange={toggleNotifications}
              trackColor={{ false: '#374151', true: '#10B981' }}
              thumbColor="#FFFFFF"
            />
          </View>
          <Text style={styles.sectionDescription}>
            Send Ring-style push notifications when family members are detected.
          </Text>
          {settings.pushNotificationsEnabled && (
            <View style={styles.statusContainer}>
              <Text style={styles.statusText}>
                ✅ Notifications enabled: {isNotificationEnabled ? 'Ready' : 'Setup required'}
              </Text>
            </View>
          )}
        </View>

        {/* App Routines */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>📱 App Routines</Text>
            <Switch
              value={settings.appRoutinesEnabled}
              onValueChange={toggleAppRoutines}
              trackColor={{ false: '#374151', true: '#10B981' }}
              thumbColor="#FFFFFF"
              disabled={settings.homeAssistantEnabled}
            />
          </View>
          <Text style={styles.sectionDescription}>
            Use app-based automation routines for users without Home Assistant.
          </Text>
          
          {settings.appRoutinesEnabled && (
            <View style={styles.routineContainer}>
              <Text style={styles.routineTitle}>Select Routine:</Text>
              {appRoutines.map((routine) => (
                <TouchableOpacity
                  key={routine.id}
                  style={[
                    styles.routineOption,
                    settings.selectedRoutine === routine.id && styles.routineOptionSelected
                  ]}
                  onPress={() => selectRoutine(routine.id)}
                >
                  <View style={styles.routineInfo}>
                    <Text style={styles.routineName}>{routine.name}</Text>
                    <Text style={styles.routineDescription}>{routine.description}</Text>
                    <View style={styles.routineActions}>
                      {routine.actions.map((action, index) => (
                        <Text key={index} style={styles.routineAction}>• {action}</Text>
                      ))}
                    </View>
                  </View>
                  {settings.selectedRoutine === routine.id && (
                    <Text style={styles.selectedIndicator}>✅</Text>
                  )}
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>

        {/* Test Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🧪 Test Current Setup</Text>
          <Text style={styles.sectionDescription}>
            Test your current automation configuration to ensure everything works as expected.
          </Text>
          <TouchableOpacity style={styles.testButton} onPress={testCurrentSetup}>
            <Text style={styles.testButtonText}>🚀 Test Automation</Text>
          </TouchableOpacity>
        </View>

        {/* Save Button */}
        <View style={styles.saveSection}>
          <TouchableOpacity
            style={[styles.saveButton, isSaving && styles.saveButtonDisabled]}
            onPress={saveSettings}
            disabled={isSaving}
          >
            {isSaving ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.saveButtonText}>💾 Save Settings</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Current Configuration Summary */}
        <View style={styles.summarySection}>
          <Text style={styles.summaryTitle}>📋 Current Configuration</Text>
          <View style={styles.summaryContainer}>
            <Text style={styles.summaryItem}>
              🏠 Home Assistant: {settings.homeAssistantEnabled ? 'Enabled' : 'Disabled'}
            </Text>
            <Text style={styles.summaryItem}>
              🔔 Push Notifications: {settings.pushNotificationsEnabled ? 'Enabled' : 'Disabled'}
            </Text>
            <Text style={styles.summaryItem}>
              📱 App Routines: {settings.appRoutinesEnabled ? 'Enabled' : 'Disabled'}
            </Text>
            {settings.appRoutinesEnabled && (
              <Text style={styles.summaryItem}>
                🎯 Selected Routine: {getSelectedRoutine()?.name}
              </Text>
            )}
          </View>
        </View>

      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#94a3b8',
    marginTop: 12,
  },
  header: {
    marginBottom: 30,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#94a3b8',
    textAlign: 'center',
    lineHeight: 22,
  },
  section: {
    marginBottom: 30,
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    flex: 1,
  },
  sectionDescription: {
    fontSize: 14,
    color: '#94a3b8',
    lineHeight: 20,
    marginBottom: 12,
  },
  statusContainer: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  statusText: {
    fontSize: 14,
    color: '#10b981',
    marginBottom: 4,
  },
  routineContainer: {
    marginTop: 16,
  },
  routineTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e2e8f0',
    marginBottom: 12,
  },
  routineOption: {
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  routineOptionSelected: {
    borderColor: '#10b981',
    backgroundColor: '#064e3b',
  },
  routineInfo: {
    flex: 1,
  },
  routineName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  routineDescription: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 8,
  },
  routineActions: {
    marginTop: 4,
  },
  routineAction: {
    fontSize: 12,
    color: '#64748b',
    marginBottom: 2,
  },
  selectedIndicator: {
    fontSize: 18,
    color: '#10b981',
    marginLeft: 12,
  },
  testButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  testButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  saveSection: {
    marginBottom: 20,
  },
  saveButton: {
    backgroundColor: '#10b981',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    backgroundColor: '#64748b',
  },
  saveButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
  },
  summarySection: {
    marginBottom: 30,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 12,
  },
  summaryContainer: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
  },
  summaryItem: {
    fontSize: 14,
    color: '#e2e8f0',
    marginBottom: 8,
  },
})

export default AutomationSettingsScreen