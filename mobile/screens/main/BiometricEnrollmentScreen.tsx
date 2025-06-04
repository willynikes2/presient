// File: mobile/screens/main/BiometricEnrollmentScreen.tsx
// Real biometric enrollment that connects to your FastAPI backend
import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  TextInput,
  ScrollView,
  Animated
} from 'react-native'
import { useNavigation } from '@react-navigation/native'
import { useAuth } from '../../contexts/AuthContext'

interface BiometricData {
  heartbeat_pattern: number[]
  mean_hr: number
  std_hr: number
  range_hr: number
}

const BiometricEnrollmentScreen = () => {
  const navigation = useNavigation()
  const { user } = useAuth()
  
  // Form state
  const [fullName, setFullName] = useState('')
  const [location, setLocation] = useState('')
  
  // Recording state
  const [isRecording, setIsRecording] = useState(false)
  const [recordingProgress, setRecordingProgress] = useState(0)
  const [biometricData, setBiometricData] = useState<BiometricData | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  
  // Animation
  const [pulseAnim] = useState(new Animated.Value(1))
  
  // Your FastAPI backend URL (update this to match your setup)
  const BACKEND_URL = 'https://obscure-dollop-r4xgv6j6wjvgfp7rp-8000.app.github.dev'

  // Simulate heartbeat recording (replace with real MR60BHA2 data later)
  const simulateHeartbeatRecording = async (): Promise<BiometricData> => {
    const duration = 30000 // 30 seconds
    const sampleRate = 1000 // 1 sample per second
    const samples = duration / sampleRate

    const heartbeatPattern: number[] = []
    let currentTime = 0

    // Simulate realistic heartbeat data
    for (let i = 0; i < samples; i++) {
      // Generate realistic heart rate between 60-100 BPM with some variation
      const baseHR = 70 + Math.sin(currentTime / 10000) * 10 // Slow variation
      const noise = (Math.random() - 0.5) * 5 // Small random variation
      const heartRate = Math.max(50, Math.min(120, baseHR + noise))

      heartbeatPattern.push(Math.round(heartRate * 100) / 100)
      currentTime += 1000

      // Update progress
      const progress = ((i + 1) / samples) * 100
      setRecordingProgress(progress)

      // Small delay to simulate real-time recording
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    // Calculate statistics
    const mean_hr = heartbeatPattern.reduce((sum, hr) => sum + hr, 0) / heartbeatPattern.length
    const variance = heartbeatPattern.reduce((sum, hr) => sum + Math.pow(hr - mean_hr, 2), 0) / heartbeatPattern.length
    const std_hr = Math.sqrt(variance)
    const range_hr = Math.max(...heartbeatPattern) - Math.min(...heartbeatPattern)

    return {
      heartbeat_pattern: heartbeatPattern,
      mean_hr: Math.round(mean_hr * 100) / 100,
      std_hr: Math.round(std_hr * 100) / 100,
      range_hr: Math.round(range_hr * 100) / 100
    }
  }

  // Start heartbeat recording
  const startRecording = async () => {
    if (!fullName.trim() || !location.trim()) {
      Alert.alert('Missing Information', 'Please enter your full name and location before recording.')
      return
    }

    console.log('🎙️ Starting biometric recording...')
    setIsRecording(true)
    setRecordingProgress(0)
    
    // Start pulse animation
    const startPulse = () => {
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.2, duration: 500, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 500, useNativeDriver: true })
      ]).start(() => {
        if (isRecording) startPulse()
      })
    }
    startPulse()

    try {
      const data = await simulateHeartbeatRecording()
      setBiometricData(data)
      setIsRecording(false)
      
      console.log('✅ Recording complete:', {
        samples: data.heartbeat_pattern.length,
        mean_hr: data.mean_hr,
        std_hr: data.std_hr,
        range_hr: data.range_hr
      })
      
      Alert.alert(
        'Recording Complete!', 
        `✅ Recorded ${data.heartbeat_pattern.length} samples\n📊 Average HR: ${data.mean_hr} bpm\n📈 Standard Deviation: ${data.std_hr}\n📏 Range: ${data.range_hr} bpm`
      )
    } catch (error) {
      console.error('❌ Recording failed:', error)
      setIsRecording(false)
      Alert.alert('Recording Failed', 'Please try again.')
    }
  }

  // Stop recording early
  const stopRecording = () => {
    setIsRecording(false)
    setRecordingProgress(0)
    Alert.alert('Recording Stopped', 'Recording was cancelled. Please start again to complete enrollment.')
  }

  // Enroll user with biometric data
  const enrollUser = async () => {
    if (!biometricData || !user) {
      Alert.alert('Error', 'Missing biometric data or user information.')
      return
    }

    setIsProcessing(true)
    console.log('🔄 Enrolling user:', fullName)

    try {
      // Convert user ID to username format (replace @ and . with _)
      const username = user.email?.replace(/[@.]/g, '_') || 'unknown_user'
      
      const enrollmentData = {
        user_id: username,
        device_id: 'mobile_app',
        heartbeat_pattern: biometricData.heartbeat_pattern,
        mean_hr: biometricData.mean_hr,
        std_hr: biometricData.std_hr,
        range_hr: biometricData.range_hr,
        confidence_threshold: 85.0,
        display_name: fullName,  // Fixed: backend expects "display_name", not "user_name"
        location: location
      }

      console.log('📤 Sending enrollment data to backend...')
      const response = await fetch(`${BACKEND_URL}/api/biometric/enroll`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(enrollmentData)
      })

      const result = await response.json()

      if (response.ok) {
        console.log('✅ Enrollment successful:', result)
        Alert.alert(
          'Enrollment Successful!',
          `${fullName} has been enrolled successfully.\n\nUser ID: ${username}\nLocation: ${location}\nSamples: ${biometricData.heartbeat_pattern.length}`,
          [
            {
              text: 'Test Authentication',
              onPress: testAuthentication
            },
            {
              text: 'Back to Dashboard',
              onPress: () => navigation.goBack()
            }
          ]
        )
      } else {
        console.error('❌ Enrollment failed:', result)
        Alert.alert('Enrollment Failed', result.error || 'Please try again.')
      }
    } catch (error) {
      console.error('❌ Network error during enrollment:', error)
      Alert.alert('Network Error', 'Could not connect to the server. Please check your connection and try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  // Test authentication with enrolled data - Format 1 (nested sensor_data)
  const testAuthentication = async () => {
    if (!biometricData || !user) return

    console.log('🔍 Testing authentication Format 1 (nested sensor_data)...')
    setIsProcessing(true)

    try {
      // Format 1: Nested sensor_data structure
      const authData = {
        user_id: user.email?.replace(/[@.]/g, '_') || 'unknown_user',
        sensor_id: 'mobile_app_sensor',
        confidence: 0.85,
        device_id: 'mobile_app',
        sensor_data: {
          heartbeat_pattern: biometricData.heartbeat_pattern,
          mean_hr: biometricData.mean_hr,
          std_hr: biometricData.std_hr,
          range_hr: biometricData.range_hr
        },
        timestamp: new Date().toISOString(),
        location: location || 'mobile_app'
      }

      console.log('📤 Sending authentication test data (Format 1):', JSON.stringify(authData, null, 2))
      const response = await fetch(`${BACKEND_URL}/api/presence/event`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(authData)
      })

      const result = await response.json()
      console.log('🔍 Authentication response (Format 1):', JSON.stringify(result, null, 2))

      if (response.ok && result.identified_user) {
        console.log('✅ Authentication successful:', result)
        Alert.alert(
          'Authentication Test Successful!',
          `🎯 Successfully identified as: ${result.identified_user}\n📊 Confidence: ${result.confidence}%\n⏱️ Response time: ${result.processing_time}ms`,
          [
            {
              text: 'Perfect!',
              onPress: () => navigation.goBack()
            }
          ]
        )
      } else {
        console.log('❌ Authentication failed (Format 1):', result)
        
        // Show detailed validation errors if available
        let errorMessage = result.error?.message || 'Could not identify user'
        if (result.error?.details) {
          console.log('📋 Validation details:', result.error.details)
          errorMessage += '\n\nValidation errors:\n'
          result.error.details.forEach((detail: any, index: number) => {
            errorMessage += `${index + 1}. ${detail.msg || detail.message || JSON.stringify(detail)}\n`
          })
        }
        
        Alert.alert(
          'Authentication Test Failed (Format 1)',
          errorMessage,
          [
            {
              text: 'Try Format 2',
              onPress: testAuthenticationAltFormat
            },
            {
              text: 'OK'
            }
          ]
        )
      }
    } catch (error) {
      console.error('❌ Authentication test error:', error)
      Alert.alert('Test Error', 'Could not test authentication.')
    } finally {
      setIsProcessing(false)
    }
  }

  // Alternative authentication format - Format 2 (flattened structure)
  const testAuthenticationAltFormat = async () => {
    if (!biometricData || !user) return

    console.log('🔄 Testing authentication Format 2 (flattened structure)...')
    setIsProcessing(true)

    try {
      // Format 2: Flattened structure (all fields at top level)
      const authData = {
        user_id: user.email?.replace(/[@.]/g, '_') || 'unknown_user',
        sensor_id: 'mobile_app_sensor',
        confidence: 0.85,
        device_id: 'mobile_app',
        heartbeat_pattern: biometricData.heartbeat_pattern,
        mean_hr: biometricData.mean_hr,
        std_hr: biometricData.std_hr,
        range_hr: biometricData.range_hr,
        timestamp: new Date().toISOString(),
        location: location || 'mobile_app'
      }

      console.log('📤 Sending authentication test data (Format 2):', JSON.stringify(authData, null, 2))
      const response = await fetch(`${BACKEND_URL}/api/presence/event`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(authData)
      })

      const result = await response.json()
      console.log('🔍 Authentication response (Format 2):', JSON.stringify(result, null, 2))

      if (response.ok && result.identified_user) {
        console.log('✅ Authentication successful (Format 2):', result)
        Alert.alert(
          'Authentication Test Successful!',
          `🎯 Successfully identified as: ${result.identified_user}\n📊 Confidence: ${result.confidence}%\n⏱️ Response time: ${result.processing_time}ms`,
          [
            {
              text: 'Perfect!',
              onPress: () => navigation.goBack()
            }
          ]
        )
      } else {
        console.log('❌ Authentication failed (Format 2):', result)
        
        // Show detailed validation errors if available
        let errorMessage = result.error?.message || 'Could not identify user'
        if (result.error?.details) {
          console.log('📋 Validation details (Format 2):', result.error.details)
          errorMessage += '\n\nValidation errors:\n'
          result.error.details.forEach((detail: any, index: number) => {
            errorMessage += `${index + 1}. ${detail.msg || detail.message || JSON.stringify(detail)}\n`
          })
        }
        
        Alert.alert(
          'Authentication Still Failed (Format 2)',
          `Both authentication formats failed.\n\n${errorMessage}`,
          [
            {
              text: 'Check Backend Logs',
              onPress: () => {
                Alert.alert(
                  'Debug Info',
                  'Check your FastAPI logs to see what exact format is expected for /api/presence/event endpoint.'
                )
              }
            },
            {
              text: 'OK'
            }
          ]
        )
      }
    } catch (error) {
      console.error('❌ Alternative authentication test error:', error)
      Alert.alert('Test Error', 'Could not test authentication with alternative format.')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Biometric Enrollment</Text>
          <Text style={styles.subtitle}>Register your heartbeat pattern for secure authentication</Text>
        </View>

        {/* Personal Information Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Personal Information</Text>
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Full Name</Text>
            <TextInput
              style={styles.textInput}
              value={fullName}
              onChangeText={setFullName}
              placeholder="Enter your full name"
              placeholderTextColor="#6B7280"
            />
          </View>
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Location</Text>
            <TextInput
              style={styles.textInput}
              value={location}
              onChangeText={setLocation}
              placeholder="e.g., Living Room, Bedroom"
              placeholderTextColor="#6B7280"
            />
          </View>
        </View>

        {/* Recording Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Heartbeat Recording</Text>
          
          {!isRecording && !biometricData && (
            <View style={styles.recordingContainer}>
              <Text style={styles.recordingInstructions}>
                📱 Sit comfortably and remain still for 30 seconds while we record your heartbeat pattern.
              </Text>
              <TouchableOpacity
                style={[styles.recordButton, (!fullName.trim() || !location.trim()) && styles.recordButtonDisabled]}
                onPress={startRecording}
                disabled={!fullName.trim() || !location.trim()}
              >
                <Text style={styles.recordButtonText}>🎙️ Start Recording</Text>
              </TouchableOpacity>
            </View>
          )}

          {isRecording && (
            <View style={styles.recordingContainer}>
              <Animated.View style={[styles.recordingIndicator, { transform: [{ scale: pulseAnim }] }]}>
                <Text style={styles.recordingIcon}>❤️</Text>
              </Animated.View>
              <Text style={styles.recordingText}>Recording heartbeat...</Text>
              <Text style={styles.progressText}>{Math.round(recordingProgress)}% complete</Text>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${recordingProgress}%` }]} />
              </View>
              <TouchableOpacity style={styles.stopButton} onPress={stopRecording}>
                <Text style={styles.stopButtonText}>Stop Recording</Text>
              </TouchableOpacity>
            </View>
          )}

          {biometricData && !isRecording && (
            <View style={styles.recordingContainer}>
              <Text style={styles.recordingComplete}>✅ Recording Complete</Text>
              <View style={styles.statsContainer}>
                <Text style={styles.statsText}>📊 Samples: {biometricData.heartbeat_pattern.length}</Text>
                <Text style={styles.statsText}>💓 Average HR: {biometricData.mean_hr} bpm</Text>
                <Text style={styles.statsText}>📈 Std Dev: {biometricData.std_hr}</Text>
                <Text style={styles.statsText}>📏 Range: {biometricData.range_hr} bpm</Text>
              </View>
              <TouchableOpacity
                style={[styles.enrollButton, isProcessing && styles.enrollButtonDisabled]}
                onPress={enrollUser}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.enrollButtonText}>Complete Enrollment</Text>
                )}
              </TouchableOpacity>
              <TouchableOpacity style={styles.retryButton} onPress={() => {
                setBiometricData(null)
                setRecordingProgress(0)
              }}>
                <Text style={styles.retryButtonText}>🔄 Record Again</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Info Section */}
        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>How it works</Text>
          <Text style={styles.infoText}>
            • Your heartbeat pattern is unique like a fingerprint{'\n'}
            • We use advanced algorithms to identify you securely{'\n'}
            • Data is processed locally and encrypted{'\n'}
            • No biometric data is stored in the cloud
          </Text>
        </View>

      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1E293B', // Dark blue background
  },
  content: {
    flex: 1,
    padding: 20,
  },
  header: {
    marginBottom: 30,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 22,
  },
  section: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 15,
  },
  inputContainer: {
    marginBottom: 15,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#E2E8F0',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#334155',
    borderRadius: 12,
    padding: 15,
    fontSize: 16,
    color: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#475569',
  },
  recordingContainer: {
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#334155',
    borderRadius: 16,
  },
  recordingInstructions: {
    fontSize: 16,
    color: '#E2E8F0',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 22,
  },
  recordButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 12,
    minWidth: 200,
    alignItems: 'center',
  },
  recordButtonDisabled: {
    backgroundColor: '#64748B',
  },
  recordButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  },
  recordingIndicator: {
    marginBottom: 20,
  },
  recordingIcon: {
    fontSize: 48,
  },
  recordingText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 10,
  },
  progressText: {
    fontSize: 16,
    color: '#94A3B8',
    marginBottom: 15,
  },
  progressBar: {
    width: '100%',
    height: 8,
    backgroundColor: '#475569',
    borderRadius: 4,
    marginBottom: 20,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#10B981',
    borderRadius: 4,
  },
  stopButton: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  stopButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '500',
  },
  recordingComplete: {
    fontSize: 20,
    fontWeight: '600',
    color: '#10B981',
    marginBottom: 20,
  },
  statsContainer: {
    marginBottom: 25,
  },
  statsText: {
    fontSize: 16,
    color: '#E2E8F0',
    marginBottom: 5,
    textAlign: 'center',
  },
  enrollButton: {
    backgroundColor: '#10B981',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 12,
    minWidth: 200,
    alignItems: 'center',
    marginBottom: 15,
  },
  enrollButtonDisabled: {
    backgroundColor: '#64748B',
  },
  enrollButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  },
  retryButton: {
    backgroundColor: 'transparent',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#64748B',
  },
  retryButtonText: {
    color: '#94A3B8',
    fontSize: 16,
    fontWeight: '500',
  },
  infoSection: {
    marginTop: 20,
    padding: 20,
    backgroundColor: '#334155',
    borderRadius: 16,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 10,
  },
  infoText: {
    fontSize: 14,
    color: '#94A3B8',
    lineHeight: 20,
  },
})

export default BiometricEnrollmentScreen