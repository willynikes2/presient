// screens/main/AutomationSettingsScreen.tsx - Decoupled Automation System
import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native'
import AsyncStorage from '@react-native-async-storage/async-storage'

interface AutomationSettings {
  homeAssistantEnabled: boolean
  pushNotificationsEnabled: boolean
  appRoutinesEnabled: boolean
  selectedRoutine: 'notification_only' | 'sound_haptic' | 'webhook' | 'custom'
  webhookUrl: string
}

interface SensorSettings {
  [sensorId: string]: AutomationSettings
}

export default function AutomationSettingsScreen() {
  const [settings, setSettings] = useState<SensorSettings>({})
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const savedSettings = await AsyncStorage.getItem('automation_settings')
      if (savedSettings) {
        setSettings(JSON.parse(savedSettings))
      } else {
        // Default settings for known sensors
        const defaultSettings: SensorSettings = {
          'mobile_app_sensor': {
            homeAssistantEnabled: true,
            pushNotificationsEnabled: true,
            appRoutinesEnabled: false,
            selectedRoutine: 'notification_only',
            webhookUrl: ''
          },
          'front_door_sensor': {
            homeAssistantEnabled: true,
            pushNotificationsEnabled: true,
            appRoutinesEnabled: false,
            selectedRoutine: 'sound_haptic',
            webhookUrl: ''
          }
        }
        setSettings(defaultSettings)
        await saveSettings(defaultSettings)
      }
    } catch (error) {
      console.error('❌ Error loading automation settings:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const saveSettings = async (newSettings: SensorSettings) => {
    try {
      await AsyncStorage.setItem('automation_settings', JSON.stringify(newSettings))
      console.log('✅ Automation settings saved')
    } catch (error) {
      console.error('❌ Error saving automation settings:', error)
    }
  }

  const updateSensorSetting = async (sensorId: string, key: keyof AutomationSettings, value: any) => {
    const newSettings = {
      ...settings,
      [sensorId]: {
        ...settings[sensorId],
        [key]: value
      }
    }
    
    setSettings(newSettings)
    await saveSettings(newSettings)
  }

  const resetToDefaults = () => {
    Alert.alert(
      'Reset Settings',
      'This will reset all automation settings to defaults. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Reset', 
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('automation_settings')
            loadSettings()
          }
        }
      ]
    )
  }

  const getRoutineDescription = (routine: string) => {
    switch (routine) {
      case 'notification_only': return 'Push notification only'
      case 'sound_haptic': return 'Notification + sound + vibration'
      case 'webhook': return 'Custom webhook trigger'
      case 'custom': return 'Custom automation'
      default: return 'Unknown routine'
    }
  }

  const renderSensorSettings = (sensorId: string, sensorSettings: AutomationSettings) => (
    <View key={sensorId} style={styles.sensorContainer}>
      <Text style={styles.sensorTitle}>
        📡 {sensorId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
      </Text>
      
      {/* Home Assistant Integration */}
      <View style={styles.settingRow}>
        <View style={styles.settingInfo}>
          <Text style={styles.settingLabel}>Home Assistant Integration</Text>
          <Text style={styles.settingDescription}>
            Use Home Assistant automations (advanced users)
          </Text>
        </View>
        <Switch
          value={sensorSettings.homeAssistantEnabled}
          onValueChange={(value) => updateSensorSetting(sensorId, 'homeAssistantEnabled', value)}
          trackColor={{ false: '#374151', true: '#3b82f6' }}
          thumbColor={sensorSettings.homeAssistantEnabled ? '#ffffff' : '#9ca3af'}
        />
      </View>
      
      {/* Push Notifications */}
      <View style={styles.settingRow}>
        <View style={styles.settingInfo}>
          <Text style={styles.settingLabel}>Push Notifications</Text>
          <Text style={styles.settingDescription}>
            Ring-style notifications when person detected
          </Text>
        </View>
        <Switch
          value={sensorSettings.pushNotificationsEnabled}
          onValueChange={(value) => updateSensorSetting(sensorId, 'pushNotificationsEnabled', value)}
          trackColor={{ false: '#374151', true: '#3b82f6' }}
          thumbColor={sensorSettings.pushNotificationsEnabled ? '#ffffff' : '#9ca3af'}
        />
      </View>
      
      {/* App Routines (only show if HA is disabled) */}
      {!sensorSettings.homeAssistantEnabled && (
        <>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>App Routines</Text>
              <Text style={styles.settingDescription}>
                Simple automations for non-HA users
              </Text>
            </View>
            <Switch
              value={sensorSettings.appRoutinesEnabled}
              onValueChange={(value) => updateSensorSetting(sensorId, 'appRoutinesEnabled', value)}
              trackColor={{ false: '#374151', true: '#3b82f6' }}
              thumbColor={sensorSettings.appRoutinesEnabled ? '#ffffff' : '#9ca3af'}
            />
          </View>
          
          {/* Routine Selection */}
          {sensorSettings.appRoutinesEnabled && (
            <View style={styles.routineContainer}>
              <Text style={styles.routineTitle}>Select App Routine:</Text>
              
              {['notification_only', 'sound_haptic', 'webhook', 'custom'].map((routine) => (
                <TouchableOpacity
                  key={routine}
                  style={[
                    styles.routineOption,
                    sensorSettings.selectedRoutine === routine && styles.routineOptionSelected
                  ]}
                  onPress={() => updateSensorSetting(sensorId, 'selectedRoutine', routine)}
                >
                  <View style={styles.routineInfo}>
                    <Text style={[
                      styles.routineLabel,
                      sensorSettings.selectedRoutine === routine && styles.routineLabelSelected
                    ]}>
                      {getRoutineDescription(routine)}
                    </Text>
                    {routine === 'webhook' && (
                      <Text style={styles.routineDescription}>
                        Trigger custom webhook URL
                      </Text>
                    )}
                  </View>
                  {sensorSettings.selectedRoutine === routine && (
                    <Text style={styles.checkmark}>✓</Text>
                  )}
                </TouchableOpacity>
              ))}
            </View>
          )}
        </>
      )}
      
      {/* Home Assistant Info */}
      {sensorSettings.homeAssistantEnabled && (
        <View style={styles.infoContainer}>
          <Text style={styles.infoTitle}>🏠 Home Assistant Mode</Text>
          <Text style={styles.infoText}>
            Automations will be handled by your Home Assistant installation. 
            Configure YAML automations to respond to MQTT messages on topic: presient/person_detected
          </Text>
        </View>
      )}
    </View>
  )

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading settings...</Text>
      </View>
    )
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.headerContainer}>
        <Text style={styles.title}>Automation Settings</Text>
        <Text style={styles.subtitle}>
          Configure how Presient responds to detections. Choose between Home Assistant integration or simple app routines.
        </Text>
      </View>
      
      <View style={styles.philosophyContainer}>
        <Text style={styles.philosophyTitle}>🎯 Design Philosophy</Text>
        <Text style={styles.philosophyText}>
          • <Text style={styles.bold}>Power Users:</Text> Use Home Assistant for advanced automations
        </Text>
        <Text style={styles.philosophyText}>
          • <Text style={styles.bold}>Regular Users:</Text> Use app routines for simple responses
        </Text>
        <Text style={styles.philosophyText}>
          • <Text style={styles.bold}>Future Ready:</Text> Compatible with Presient Hub
        </Text>
      </View>
      
      {Object.entries(settings).map(([sensorId, sensorSettings]) =>
        renderSensorSettings(sensorId, sensorSettings)
      )}
      
      <View style={styles.actionsContainer}>
        <TouchableOpacity style={styles.resetButton} onPress={resetToDefaults}>
          <Text style={styles.resetButtonText}>🔄 Reset to Defaults</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.testButton} onPress={() => Alert.alert('Test', 'This would test the current automation settings')}>
          <Text style={styles.testButtonText}>🧪 Test Settings</Text>
        </TouchableOpacity>
      </View>
      
      <View style={styles.footerContainer}>
        <Text style={styles.footerTitle}>💡 How it Works</Text>
        <Text style={styles.footerText}>
          When a person is detected with sufficient confidence, Presient will:
        </Text>
        <Text style={styles.footerText}>
          1. Send push notification (if enabled)
        </Text>
        <Text style={styles.footerText}>
          2. Publish MQTT message (if Home Assistant enabled)
        </Text>
        <Text style={styles.footerText}>
          3. Execute app routine (if enabled and HA disabled)
        </Text>
        <Text style={styles.footerText}>
          4. Log the detection event
        </Text>
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
  },
  loadingText: {
    color: '#94a3b8',
    fontSize: 16,
  },
  headerContainer: {
    padding: 20,
    backgroundColor: '#1e293b',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#94a3b8',
    lineHeight: 22,
  },
  philosophyContainer: {
    backgroundColor: '#1e293b',
    margin: 20,
    padding: 16,
    borderRadius: 12,
  },
  philosophyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
  },
  philosophyText: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 6,
  },
  bold: {
    fontWeight: 'bold',
    color: '#e2e8f0',
  },
  sensorContainer: {
    backgroundColor: '#1e293b',
    margin: 20,
    marginTop: 0,
    padding: 20,
    borderRadius: 12,
  },
  sensorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  settingInfo: {
    flex: 1,
    marginRight: 12,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 14,
    color: '#94a3b8',
  },
  routineContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#374151',
  },
  routineTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 12,
  },
  routineOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: '#374151',
  },
  routineOptionSelected: {
    backgroundColor: '#3b82f6',
  },
  routineInfo: {
    flex: 1,
  },
  routineLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  routineLabelSelected: {
    color: '#ffffff',
  },
  routineDescription: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
  },
  checkmark: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  infoContainer: {
    backgroundColor: '#065f46',
    padding: 16,
    borderRadius: 8,
    marginTop: 16,
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 12,
    color: '#d1fae5',
    lineHeight: 16,
  },
  actionsContainer: {
    flexDirection: 'row',
    margin: 20,
    gap: 12,
  },
  resetButton: {
    flex: 1,
    backgroundColor: '#374151',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  resetButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  testButton: {
    flex: 1,
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  testButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  footerContainer: {
    backgroundColor: '#1e293b',
    margin: 20,
    marginTop: 0,
    padding: 16,
    borderRadius: 12,
  },
  footerTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
  },
  footerText: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 6,
  },
})