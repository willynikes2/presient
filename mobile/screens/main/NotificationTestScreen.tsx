// Notification Test Screen - Ring-Style Testing
// mobile/screens/main/NotificationTestScreen.tsx

import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
  ActivityIndicator
} from 'react-native'
import { useNavigation } from '@react-navigation/native'
import { useAuth } from '../../contexts/AuthContext'
import { useNotifications } from '../../contexts/NotificationContext'

interface TestNotification {
  id: string
  title: string
  body: string
  person: string
  sensor: string
  confidence: number
  description: string
}

const NotificationTestScreen = () => {
  const navigation = useNavigation()
  const { user } = useAuth()
  const { 
    expoPushToken, 
    isNotificationEnabled, 
    setupNotifications, 
    sendTestNotification,
    sendPresenceNotification 
  } = useNotifications()
  
  const [isSetupLoading, setIsSetupLoading] = useState(false)

  // Test notification scenarios
  const testNotifications: TestNotification[] = [
    {
      id: 'high_confidence',
      title: '🏠 John Smith detected',
      body: 'Recognized at Front Door with 95.8% confidence',
      person: 'john_smith',
      sensor: 'front_door_sensor',
      confidence: 95.8,
      description: 'High confidence detection - typical successful recognition'
    },
    {
      id: 'family_member',
      title: '🏠 Sarah detected',
      body: 'Recognized at Living Room with 89.2% confidence',
      person: 'sarah_jones',
      sensor: 'living_room_sensor',
      confidence: 89.2,
      description: 'Family member detection with good confidence'
    },
    {
      id: 'dual_sensor',
      title: '🏠 Mike Johnson detected',
      body: 'Recognized at Kitchen with 99.1% confidence (Dual-Sensor)',
      person: 'mike_johnson',
      sensor: 'kitchen_sensor',
      confidence: 99.1,
      description: 'Dual-sensor detection (Phone + Apple Watch) - highest accuracy'
    },
    {
      id: 'mobile_app',
      title: '🏠 testimg2_gnail_cm detected',
      body: 'Recognized at Mobile Sensor with 97.4% confidence',
      person: 'testimg2_gnail_cm',
      sensor: 'mobile_app_sensor',
      confidence: 97.4,
      description: 'Mobile app biometric authentication - your actual user'
    },
    {
      id: 'low_confidence',
      title: '🏠 Unknown Person detected',
      body: 'Unrecognized detection at Entry Point with 67.3% confidence',
      person: 'unknown_person',
      sensor: 'entry_sensor',
      confidence: 67.3,
      description: 'Low confidence detection - might not trigger automations'
    },
    {
      id: 'watch_fallback',
      title: '🏠 Emily Chen detected',
      body: 'Recognized at Bedroom with 81.5% confidence (Apple Watch)',
      person: 'emily_chen',
      sensor: 'bedroom_sensor',
      confidence: 81.5,
      description: 'Apple Watch fallback when phone sensor unavailable'
    }
  ]

  const setupRingNotifications = async () => {
    try {
      setIsSetupLoading(true)
      console.log('🔔 Setting up Ring-style notifications...')
      
      const success = await setupNotifications()
      
      if (success) {
        Alert.alert(
          '✅ Notifications Ready!',
          'Ring-style notifications are now enabled. You can test different scenarios below.',
          [{ text: 'Great!' }],
          { userInterfaceStyle: 'dark' }
        )
      }
      
    } catch (error) {
      console.error('❌ Notification setup error:', error)
      Alert.alert(
        '❌ Setup Failed',
        'Could not setup notifications. Please check permissions and try again.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
    } finally {
      setIsSetupLoading(false)
    }
  }

  const sendTestNotificationScenario = async (notification: TestNotification) => {
    try {
      console.log(`🧪 Testing Ring-style notification: ${notification.id}`)
      
      await sendPresenceNotification(
        notification.person,
        notification.sensor,
        notification.confidence
      )
      
      Alert.alert(
        '🔔 Notification Sent!',
        `Ring-style notification sent for "${notification.person}". Check your notification tray!`,
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
      
    } catch (error) {
      console.error('❌ Test notification error:', error)
      Alert.alert(
        '❌ Test Failed',
        'Could not send test notification. Please ensure notifications are enabled.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
    }
  }

  const sendQuickTest = async () => {
    try {
      await sendTestNotification()
    } catch (error) {
      console.error('❌ Quick test error:', error)
    }
  }

  const navigateToSensorDetail = (sensorId: string) => {
    // Simulate notification tap navigation
    navigation.navigate('SensorDetail' as never, { sensor: sensorId } as never)
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return '#10b981'
    if (confidence >= 80) return '#3b82f6'
    if (confidence >= 70) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.title}>🔔 Ring-Style Notifications</Text>
          <View style={styles.placeholder} />
        </View>

        {/* Setup Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚙️ Notification Setup</Text>
          <Text style={styles.sectionDescription}>
            Enable Ring-style push notifications for presence detection events.
          </Text>
          
          <View style={styles.statusContainer}>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Status:</Text>
              <Text style={[
                styles.statusValue,
                { color: isNotificationEnabled ? '#10b981' : '#f59e0b' }
              ]}>
                {isNotificationEnabled ? '✅ Enabled' : '⚠️ Setup Required'}
              </Text>
            </View>
            
            {expoPushToken && (
              <View style={styles.statusRow}>
                <Text style={styles.statusLabel}>Push Token:</Text>
                <Text style={styles.statusValue}>
                  {expoPushToken.substring(0, 20)}...
                </Text>
              </View>
            )}
          </View>

          {!isNotificationEnabled && (
            <TouchableOpacity
              style={[styles.setupButton, isSetupLoading && styles.setupButtonDisabled]}
              onPress={setupRingNotifications}
              disabled={isSetupLoading}
            >
              {isSetupLoading ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <Text style={styles.setupButtonText}>🚀 Enable Ring Notifications</Text>
              )}
            </TouchableOpacity>
          )}
        </View>

        {/* Quick Test */}
        {isNotificationEnabled && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>⚡ Quick Test</Text>
            <Text style={styles.sectionDescription}>
              Send a basic test notification to verify everything is working.
            </Text>
            
            <TouchableOpacity style={styles.quickTestButton} onPress={sendQuickTest}>
              <Text style={styles.quickTestButtonText}>🧪 Send Quick Test</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Test Scenarios */}
        {isNotificationEnabled && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>🎭 Test Scenarios</Text>
            <Text style={styles.sectionDescription}>
              Test different Ring-style notification scenarios to see how they appear.
            </Text>
            
            <View style={styles.scenariosList}>
              {testNotifications.map((notification) => (
                <View key={notification.id} style={styles.scenarioCard}>
                  <View style={styles.scenarioHeader}>
                    <Text style={styles.scenarioTitle}>{notification.title}</Text>
                    <View style={[
                      styles.confidenceBadge,
                      { backgroundColor: getConfidenceColor(notification.confidence) }
                    ]}>
                      <Text style={styles.confidenceText}>
                        {notification.confidence.toFixed(1)}%
                      </Text>
                    </View>
                  </View>
                  
                  <Text style={styles.scenarioBody}>{notification.body}</Text>
                  <Text style={styles.scenarioDescription}>{notification.description}</Text>
                  
                  <View style={styles.scenarioActions}>
                    <TouchableOpacity
                      style={styles.testButton}
                      onPress={() => sendTestNotificationScenario(notification)}
                    >
                      <Text style={styles.testButtonText}>📤 Send Test</Text>
                    </TouchableOpacity>
                    
                    <TouchableOpacity
                      style={styles.previewButton}
                      onPress={() => navigateToSensorDetail(notification.sensor)}
                    >
                      <Text style={styles.previewButtonText}>👁️ Preview Detail</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Ring-Style Features */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🔥 Ring-Style Features</Text>
          <View style={styles.featuresList}>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>📱</Text>
              <View style={styles.featureContent}>
                <Text style={styles.featureTitle}>Instant Notifications</Text>
                <Text style={styles.featureDescription}>
                  Get notified the moment family members are detected
                </Text>
              </View>
            </View>
            
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>👆</Text>
              <View style={styles.featureContent}>
                <Text style={styles.featureTitle}>Tap to View Details</Text>
                <Text style={styles.featureDescription}>
                  Tap notifications to see sensor data and recent activity
                </Text>
              </View>
            </View>
            
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🎯</Text>
              <View style={styles.featureContent}>
                <Text style={styles.featureTitle}>Confidence Scoring</Text>
                <Text style={styles.featureDescription}>
                  See authentication confidence for each detection
                </Text>
              </View>
            </View>
            
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>⚙️</Text>
              <View style={styles.featureContent}>
                <Text style={styles.featureTitle}>Smart Automation</Text>
                <Text style={styles.featureDescription}>
                  Integrates with Home Assistant for device control
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Navigation */}
        <View style={styles.navigationSection}>
          <TouchableOpacity
            style={styles.navButton}
            onPress={() => navigation.navigate('AutomationSettings' as never)}
          >
            <Text style={styles.navButtonText}>⚙️ Automation Settings</Text>
          </TouchableOpacity>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  backButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  backButtonText: {
    fontSize: 16,
    color: '#10b981',
    fontWeight: '500',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  placeholder: {
    width: 60,
  },
  section: {
    marginBottom: 24,
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 14,
    color: '#94a3b8',
    lineHeight: 20,
    marginBottom: 16,
  },
  statusContainer: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  statusLabel: {
    fontSize: 14,
    color: '#9ca3af',
  },
  statusValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  setupButton: {
    backgroundColor: '#10b981',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  setupButtonDisabled: {
    backgroundColor: '#64748b',
  },
  setupButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  quickTestButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  quickTestButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  scenariosList: {
    gap: 12,
  },
  scenarioCard: {
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 16,
  },
  scenarioHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  scenarioTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    flex: 1,
  },
  confidenceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  scenarioBody: {
    fontSize: 14,
    color: '#e2e8f0',
    marginBottom: 8,
  },
  scenarioDescription: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 12,
  },
  scenarioActions: {
    flexDirection: 'row',
    gap: 8,
  },
  testButton: {
    flex: 1,
    backgroundColor: '#10b981',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
  },
  testButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  previewButton: {
    flex: 1,
    backgroundColor: '#6366f1',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
  },
  previewButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  featuresList: {
    gap: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  featureIcon: {
    fontSize: 24,
    marginRight: 12,
    marginTop: 2,
  },
  featureContent: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  featureDescription: {
    fontSize: 14,
    color: '#94a3b8',
    lineHeight: 18,
  },
  navigationSection: {
    marginBottom: 20,
  },
  navButton: {
    backgroundColor: '#374151',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  navButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
})

export default NotificationTestScreen