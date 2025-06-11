// screens/main/NotificationTestScreen.tsx - Ring-Style Notification Testing
import React, { useState } from 'react'
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
} from 'react-native'
import { useNotifications } from '../../contexts/NotificationContext'

export default function NotificationTestScreen() {
  const { 
    expoPushToken, 
    notificationsEnabled, 
    sendTestNotification, 
    enableNotifications,
    sendDetectionNotification 
  } = useNotifications()
  
  const [testPerson, setTestPerson] = useState('testimg2_gnail_cm')
  const [testSensor, setTestSensor] = useState('mobile_app_sensor')
  const [testConfidence, setTestConfidence] = useState('99.1')

  const handleEnableNotifications = async () => {
    const success = await enableNotifications()
    if (success) {
      Alert.alert('Success', 'Ring-style notifications enabled!')
    } else {
      Alert.alert('Error', 'Failed to enable notifications. Please check your device settings.')
    }
  }

  const handleTestBasicNotification = async () => {
    await sendTestNotification()
    Alert.alert('Test Sent', 'Ring-style test notification sent!')
  }

  const handleTestDetectionNotification = async () => {
    const confidence = parseFloat(testConfidence) / 100
    await sendDetectionNotification(testPerson, testSensor, confidence)
    Alert.alert('Detection Test', 'Ring-style detection notification sent!')
  }

  const handleTestScenarios = () => {
    Alert.alert(
      'Test Scenarios',
      'Choose a scenario to test:',
      [
        {
          text: 'High Confidence (95%)',
          onPress: () => sendDetectionNotification('john_smith', 'front_door_sensor', 0.95)
        },
        {
          text: 'Medium Confidence (85%)',
          onPress: () => sendDetectionNotification('jane_doe', 'back_door_sensor', 0.85)
        },
        {
          text: 'Low Confidence (75%)',
          onPress: () => sendDetectionNotification('unknown_person', 'garage_sensor', 0.75)
        },
        { text: 'Cancel', style: 'cancel' }
      ]
    )
  }

  const renderStatus = () => (
    <View style={styles.statusContainer}>
      <Text style={styles.sectionTitle}>📱 Notification Status</Text>
      
      <View style={styles.statusRow}>
        <Text style={styles.statusLabel}>Notifications Enabled:</Text>
        <Text style={[styles.statusValue, { color: notificationsEnabled ? '#10b981' : '#ef4444' }]}>
          {notificationsEnabled ? '✅ Yes' : '❌ No'}
        </Text>
      </View>
      
      <View style={styles.statusRow}>
        <Text style={styles.statusLabel}>Push Token:</Text>
        <Text style={styles.statusValue}>
          {expoPushToken ? '✅ Generated' : '❌ Missing'}
        </Text>
      </View>
      
      {expoPushToken && (
        <View style={styles.tokenContainer}>
          <Text style={styles.tokenLabel}>Token (for backend):</Text>
          <Text style={styles.tokenValue} numberOfLines={3}>
            {expoPushToken}
          </Text>
        </View>
      )}
    </View>
  )

  const renderBasicTests = () => (
    <View style={styles.testContainer}>
      <Text style={styles.sectionTitle}>🧪 Basic Tests</Text>
      
      {!notificationsEnabled ? (
        <TouchableOpacity style={styles.enableButton} onPress={handleEnableNotifications}>
          <Text style={styles.enableButtonText}>🔔 Enable Ring-Style Notifications</Text>
        </TouchableOpacity>
      ) : (
        <>
          <TouchableOpacity style={styles.testButton} onPress={handleTestBasicNotification}>
            <Text style={styles.testButtonText}>📨 Send Test Notification</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.testButton} onPress={handleTestScenarios}>
            <Text style={styles.testButtonText}>🎭 Test Scenarios</Text>
          </TouchableOpacity>
        </>
      )}
    </View>
  )

  const renderCustomTest = () => (
    <View style={styles.customContainer}>
      <Text style={styles.sectionTitle}>⚙️ Custom Detection Test</Text>
      
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Person ID:</Text>
        <TextInput
          style={styles.textInput}
          value={testPerson}
          onChangeText={setTestPerson}
          placeholder="testimg2_gnail_cm"
          placeholderTextColor="#64748b"
        />
      </View>
      
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Sensor:</Text>
        <TextInput
          style={styles.textInput}
          value={testSensor}
          onChangeText={setTestSensor}
          placeholder="mobile_app_sensor"
          placeholderTextColor="#64748b"
        />
      </View>
      
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Confidence (%):</Text>
        <TextInput
          style={styles.textInput}
          value={testConfidence}
          onChangeText={setTestConfidence}
          placeholder="99.1"
          placeholderTextColor="#64748b"
          keyboardType="numeric"
        />
      </View>
      
      <TouchableOpacity 
        style={[styles.testButton, !notificationsEnabled && styles.disabledButton]} 
        onPress={handleTestDetectionNotification}
        disabled={!notificationsEnabled}
      >
        <Text style={[styles.testButtonText, !notificationsEnabled && styles.disabledText]}>
          🚀 Send Custom Detection
        </Text>
      </TouchableOpacity>
    </View>
  )

  const renderExpectedBehavior = () => (
    <View style={styles.infoContainer}>
      <Text style={styles.sectionTitle}>💡 Expected Behavior</Text>
      
      <Text style={styles.infoText}>
        <Text style={styles.bold}>Ring-Style Notifications:</Text>
      </Text>
      <Text style={styles.infoText}>• Show even when app is closed</Text>
      <Text style={styles.infoText}>• Play notification sound</Text>
      <Text style={styles.infoText}>• Display confidence percentage</Text>
      <Text style={styles.infoText}>• Tap to open sensor detail screen</Text>
      
      <Text style={styles.infoText}>
        <Text style={styles.bold}>Notification Format:</Text>
      </Text>
      <Text style={styles.infoText}>🔍 [person] detected</Text>
      <Text style={styles.infoText}>Recognized at [sensor] with [confidence]% confidence</Text>
      
      <Text style={styles.infoText}>
        <Text style={styles.bold}>Navigation:</Text>
      </Text>
      <Text style={styles.infoText}>• Tap notification → Opens sensor detail screen</Text>
      <Text style={styles.infoText}>• Shows detection history and statistics</Text>
    </View>
  )

  return (
    <ScrollView style={styles.container}>
      <View style={styles.headerContainer}>
        <Text style={styles.title}>🔔 Ring-Style Notifications</Text>
        <Text style={styles.subtitle}>
          Test the complete notification experience. This is how we beat Ring!
        </Text>
      </View>
      
      {renderStatus()}
      {renderBasicTests()}
      {renderCustomTest()}
      {renderExpectedBehavior()}
      
      <View style={styles.footerContainer}>
        <Text style={styles.footerTitle}>🎯 Integration Ready</Text>
        <Text style={styles.footerText}>
          Once notifications work here, your backend can send real Ring-style notifications when biometric authentication succeeds.
        </Text>
        <Text style={styles.footerText}>
          Expected flow: Authentication → MQTT → Home Assistant → Shield + Push Notification
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
  statusContainer: {
    backgroundColor: '#1e293b',
    margin: 20,
    padding: 20,
    borderRadius: 12,
  },
  testContainer: {
    backgroundColor: '#1e293b',
    margin: 20,
    marginTop: 0,
    padding: 20,
    borderRadius: 12,
  },
  customContainer: {
    backgroundColor: '#1e293b',
    margin: 20,
    marginTop: 0,
    padding: 20,
    borderRadius: 12,
  },
  infoContainer: {
    backgroundColor: '#1e293b',
    margin: 20,
    marginTop: 0,
    padding: 20,
    borderRadius: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  statusLabel: {
    fontSize: 16,
    color: '#e2e8f0',
  },
  statusValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  tokenContainer: {
    marginTop: 16,
    padding: 16,
    backgroundColor: '#374151',
    borderRadius: 8,
  },
  tokenLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e2e8f0',
    marginBottom: 8,
  },
  tokenValue: {
    fontSize: 12,
    color: '#94a3b8',
    fontFamily: 'monospace',
  },
  enableButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  enableButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  testButton: {
    backgroundColor: '#10b981',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  testButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  disabledButton: {
    backgroundColor: '#374151',
  },
  disabledText: {
    color: '#94a3b8',
  },
  inputContainer: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e2e8f0',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#374151',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    fontSize: 16,
    color: '#ffffff',
    borderWidth: 1,
    borderColor: '#475569',
  },
  infoText: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 6,
    lineHeight: 20,
  },
  bold: {
    fontWeight: 'bold',
    color: '#e2e8f0',
  },
  footerContainer: {
    backgroundColor: '#065f46',
    margin: 20,
    marginTop: 0,
    padding: 20,
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
    color: '#d1fae5',
    marginBottom: 8,
    lineHeight: 20,
  },
})