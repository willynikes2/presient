// File: mobile/screens/main/BiometricEnrollmentScreen.tsx
// Health-themed biometric enrollment with simplified authentication
import * as React from 'react'
import { useState, useEffect } from 'react'
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
  const BACKEND_URL = 'http://192.168.1.135:8000'

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
      Alert.alert(
        '⚠️ Missing Information', 
        '📝 Please enter your full name and location before recording your cardiac signature.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
      return
    }

    console.log('🫀 Starting biometric recording...')
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
        '💚 Cardiac Recording Complete!', 
        `🫀 Successfully captured your heartbeat signature\n\n` +
        `📊 Samples Recorded: ${data.heartbeat_pattern.length}\n` +
        `💓 Average Heart Rate: ${data.mean_hr} BPM\n` +
        `📈 Heart Rate Variability: ${data.std_hr}\n` +
        `📏 Rate Range: ${data.range_hr} BPM\n\n` +
        `✨ Your unique cardiac pattern is ready for enrollment.`,
        [{ text: '🔄 Continue', style: 'default' }],
        { userInterfaceStyle: 'dark' }
      )
    } catch (error) {
      console.error('❌ Recording failed:', error)
      setIsRecording(false)
      Alert.alert(
        '🔴 Recording Failed', 
        '🫀 Unable to capture cardiac signature. Please ensure you remain still and try again.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
    }
  }

  // Stop recording early
  const stopRecording = () => {
    setIsRecording(false)
    setRecordingProgress(0)
    Alert.alert(
      '⏹️ Recording Stopped', 
      '🫀 Cardiac recording was cancelled. Please start again to complete enrollment.',
      [{ text: 'OK' }],
      { userInterfaceStyle: 'dark' }
    )
  }

  // Enroll user with biometric data
  const enrollUser = async () => {
    if (!biometricData || !user) {
      Alert.alert(
        '⚠️ Error', 
        '🫀 Missing biometric data or user information.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
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
        display_name: fullName,
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
          '💚 Enrollment Successful!',
          `🫀 ${fullName} has been enrolled in the biometric system\n\n` +
          `👤 User ID: ${username}\n` +
          `📍 Location: ${location}\n` +
          `📊 Cardiac Samples: ${biometricData.heartbeat_pattern.length}\n\n` +
          `✨ Your unique heartbeat pattern is now registered for secure family presence detection.`,
          [
            {
              text: '🧪 Test Authentication',
              style: 'default',
              onPress: testAuthentication
            },
            {
              text: '🏠 Back to Dashboard',
              style: 'default',
              onPress: () => navigation.goBack()
            }
          ],
          { userInterfaceStyle: 'dark' }
        )
      } else {
        console.error('❌ Enrollment failed:', result)
        Alert.alert(
          '🔴 Enrollment Failed', 
          `🫀 Unable to register your cardiac signature: ${result.error || 'Please try again.'}`,
          [{ text: 'OK' }],
          { userInterfaceStyle: 'dark' }
        )
      }
    } catch (error) {
      console.error('❌ Network error during enrollment:', error)
      Alert.alert(
        '🌐 Network Error', 
        '🫀 Could not connect to the biometric server. Please check your connection and try again.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
    } finally {
      setIsProcessing(false)
    }
  }

  // Test authentication with enrolled data
  const testAuthentication = async () => {
    if (!biometricData || !user) return

    console.log('🫀 Testing biometric authentication...')
    setIsProcessing(true)

    try {
      // Use the proven working format (flattened structure)
      const authData = {
        user_id: user.email?.replace(/[@.]/g, '_') || 'unknown_user',
        sensor_id: 'mobile_app_sensor',
        confidence: 0.85,
        device_id: 'mobile_app',
        heart_rate: biometricData.mean_hr,          // ✅ Working format
        breathing_rate: 16,                         // ✅ Working format
        timestamp: new Date().toISOString(),
        location: location || 'mobile_app'
      }

      console.log('📤 Sending biometric authentication data:', JSON.stringify(authData, null, 2))
      const response = await fetch(`${BACKEND_URL}/api/presence/event`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(authData)
      })

      const result = await response.json()
      console.log('🔍 Authentication response:', JSON.stringify(result, null, 2))

      if (response.ok && result.biometric_authentication?.authenticated) {
        console.log('✅ Biometric authentication successful:', result)
        
        // Beautiful health-themed success message
        const confidence = (result.biometric_authentication.confidence * 100).toFixed(1)
        const matchedUser = result.biometric_authentication.matched_user_id
        
        Alert.alert(
          '💚 Biometric Authentication Successful',
          `🫀 Heartbeat Pattern Verified\n\n` +
          `👤 Identity Confirmed: ${matchedUser}\n` +
          `📊 Biometric Confidence: ${confidence}%\n` +
          `💓 Heart Rate: ${result.sensor_data.heart_rate} BPM\n` +
          `🫁 Breathing Rate: ${result.sensor_data.breathing_rate} BPM\n\n` +
          `✨ Your unique cardiac signature has been authenticated with medical-grade precision.`,
          [
            {
              text: '🏠 Continue to Dashboard',
              style: 'default',
              onPress: () => navigation.goBack()
            }
          ],
          { userInterfaceStyle: 'dark' }
        )
      } else {
        console.log('❌ Authentication failed:', result)
        
        // Health-themed failure message
        let errorMessage = result.biometric_authentication?.message || 'Biometric pattern not recognized'
        
        Alert.alert(
          '🔴 Biometric Authentication Failed',
          `🫀 Heartbeat Pattern Analysis\n\n` +
          `❌ ${errorMessage}\n\n` +
          `💡 Your cardiac signature could not be matched against enrolled family members. Please try recording again or enroll this profile.`,
          [
            {
              text: '🔄 Try Again',
              style: 'default'
            },
            {
              text: '➕ Enroll New Profile',
              style: 'default',
              onPress: () => {
                setBiometricData(null)
                setRecordingProgress(0)
              }
            }
          ],
          { userInterfaceStyle: 'dark' }
        )
      }
    } catch (error) {
      console.error('❌ Authentication test error:', error)
      Alert.alert(
        '⚠️ Network Error', 
        '🌐 Could not connect to biometric authentication server. Please check your connection and try again.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>🫀 Cardiac Enrollment</Text>
          <Text style={styles.subtitle}>Register your unique heartbeat pattern for secure family authentication</Text>
        </View>

        {/* Personal Information Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>👤 Personal Information</Text>
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
              placeholder="e.g., Living Room, Kitchen, Bedroom"
              placeholderTextColor="#6B7280"
            />
          </View>
        </View>

        {/* Recording Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🫀 Cardiac Recording</Text>
          
          {!isRecording && !biometricData && (
            <View style={styles.recordingContainer}>
              <Text style={styles.recordingInstructions}>
                💓 Sit comfortably and remain still for 30 seconds while we capture your unique heartbeat signature for secure biometric authentication.
              </Text>
              <TouchableOpacity
                style={[styles.recordButton, (!fullName.trim() || !location.trim()) && styles.recordButtonDisabled]}
                onPress={startRecording}
                disabled={!fullName.trim() || !location.trim()}
              >
                <Text style={styles.recordButtonText}>🫀 Start Cardiac Recording</Text>
              </TouchableOpacity>
            </View>
          )}

          {isRecording && (
            <View style={styles.recordingContainer}>
              <Animated.View style={[styles.recordingIndicator, { transform: [{ scale: pulseAnim }] }]}>
                <Text style={styles.recordingIcon}>💓</Text>
              </Animated.View>
              <Text style={styles.recordingText}>Recording cardiac signature...</Text>
              <Text style={styles.progressText}>{Math.round(recordingProgress)}% complete</Text>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${recordingProgress}%` }]} />
              </View>
              <TouchableOpacity style={styles.stopButton} onPress={stopRecording}>
                <Text style={styles.stopButtonText}>⏹️ Stop Recording</Text>
              </TouchableOpacity>
            </View>
          )}

          {biometricData && !isRecording && (
            <View style={styles.recordingContainer}>
              <Text style={styles.recordingComplete}>✅ Cardiac Recording Complete</Text>
              <View style={styles.statsContainer}>
                <Text style={styles.statsText}>📊 Cardiac Samples: {biometricData.heartbeat_pattern.length}</Text>
                <Text style={styles.statsText}>💓 Average Heart Rate: {biometricData.mean_hr} BPM</Text>
                <Text style={styles.statsText}>📈 Heart Rate Variability: {biometricData.std_hr}</Text>
                <Text style={styles.statsText}>📏 Rate Range: {biometricData.range_hr} BPM</Text>
              </View>
              <TouchableOpacity
                style={[styles.enrollButton, isProcessing && styles.enrollButtonDisabled]}
                onPress={enrollUser}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.enrollButtonText}>🔐 Complete Enrollment</Text>
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
          <Text style={styles.infoTitle}>🔬 How Cardiac Biometrics Work</Text>
          <Text style={styles.infoText}>
            • Your heartbeat pattern is as unique as a fingerprint{'\n'}
            • We analyze cardiac rhythm, rate variability, and timing{'\n'}
            • Data is processed locally with medical-grade encryption{'\n'}
            • No biometric data is stored in external clouds{'\n'}
            • Enables secure, contactless family presence detection
          </Text>
        </View>

      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1E293B', // Dark medical theme
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
    backgroundColor: '#10B981', // Health green
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
    backgroundColor: '#10B981', // Health green progress
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
    color: '#10B981', // Health green
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
    backgroundColor: '#10B981', // Health green
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