// File: mobile/screens/main/DashboardScreen.tsx
import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  RefreshControl,
} from 'react-native'
import { NativeStackScreenProps } from '@react-navigation/native-stack'
import { MainStackParamList } from '../../App'
import { useAuth } from '../../contexts/AuthContext'

type Props = NativeStackScreenProps<MainStackParamList, 'Dashboard'>

interface DashboardStats {
  enrolledDevices: number
  biometricProfiles: number
  lastAuthentication?: string
  recentActivity: Array<{
    id: string
    type: 'authentication' | 'enrollment' | 'device_added'
    timestamp: string
    description: string
  }>
}

const DashboardScreen: React.FC<Props> = ({ navigation }) => {
  const { user, profile, signOut } = useAuth()
  const [stats, setStats] = useState<DashboardStats>({
    enrolledDevices: 0,
    biometricProfiles: 0,
    recentActivity: []
  })
  const [refreshing, setRefreshing] = useState(false)

  const loadDashboardData = async () => {
    try {
      // TODO: Replace with actual API calls to your FastAPI backend
      // For now, using mock data
      setStats({
        enrolledDevices: 1,
        biometricProfiles: 1,
        lastAuthentication: '2025-06-02T17:16:18.215Z',
        recentActivity: [
          {
            id: '1',
            type: 'authentication',
            timestamp: '2025-06-02T17:16:18.215Z',
            description: 'Successfully authenticated via princeton_mmwave'
          },
          {
            id: '2',
            type: 'enrollment',
            timestamp: '2025-06-02T16:24:01.079Z',
            description: 'Biometric profile enrolled'
          }
        ]
      })
    } catch (error) {
      console.error('Error loading dashboard data:', error)
    }
  }

  const onRefresh = async () => {
    setRefreshing(true)
    await loadDashboardData()
    setRefreshing(false)
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  const handleSignOut = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Sign Out', style: 'destructive', onPress: signOut }
      ]
    )
  }

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.name}>{profile?.first_name || 'User'}</Text>
        </View>
        <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut}>
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats.enrolledDevices}</Text>
          <Text style={styles.statLabel}>Enrolled Devices</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats.biometricProfiles}</Text>
          <Text style={styles.statLabel}>Biometric Profiles</Text>
        </View>
      </View>

      <View style={styles.actionsContainer}>
        <TouchableOpacity 
          style={[styles.actionCard, styles.primaryAction]}
          onPress={() => navigation.navigate('BiometricEnrollment')}
        >
          <Text style={styles.actionIcon}>❤️</Text>
          <Text style={styles.actionTitle}>Enroll Biometrics</Text>
          <Text style={styles.actionDescription}>Register your heartbeat pattern</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionCard}
          onPress={() => navigation.navigate('DeviceManagement')}
        >
          <Text style={styles.actionIcon}>📱</Text>
          <Text style={styles.actionTitle}>Manage Devices</Text>
          <Text style={styles.actionDescription}>Add or configure sensors</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionCard}
          onPress={() => navigation.navigate('Profile')}
        >
          <Text style={styles.actionIcon}>👤</Text>
          <Text style={styles.actionTitle}>Profile Settings</Text>
          <Text style={styles.actionDescription}>Update your information</Text>
        </TouchableOpacity>
      </View>

      {stats.recentActivity.length > 0 && (
        <View style={styles.activityContainer}>
          <Text style={styles.sectionTitle}>Recent Activity</Text>
          {stats.recentActivity.map((activity) => (
            <View key={activity.id} style={styles.activityItem}>
              <View style={styles.activityIcon}>
                <Text style={styles.activityIconText}>
                  {activity.type === 'authentication' ? '🔓' : 
                   activity.type === 'enrollment' ? '❤️' : '📱'}
                </Text>
              </View>
              <View style={styles.activityContent}>
                <Text style={styles.activityDescription}>{activity.description}</Text>
                <Text style={styles.activityTime}>
                  {new Date(activity.timestamp).toLocaleString()}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  )
}

// File: mobile/screens/main/BiometricEnrollmentScreen.tsx
export const BiometricEnrollmentScreen: React.FC<NativeStackScreenProps<MainStackParamList, 'BiometricEnrollment'>> = ({ navigation, route }) => {
  const { user } = useAuth()
  const [enrollmentStep, setEnrollmentStep] = useState<'intro' | 'recording' | 'processing' | 'complete'>('intro')
  const [heartbeatData, setHeartbeatData] = useState<number[]>([])
  const [recordingProgress, setRecordingProgress] = useState(0)
  const [isRecording, setIsRecording] = useState(false)

  const startEnrollment = async () => {
    setEnrollmentStep('recording')
    setIsRecording(true)
    setRecordingProgress(0)
    setHeartbeatData([])

    // Simulate heartbeat data collection for 30 seconds
    // In production, this would connect to your MR60BHA2 sensor via BLE
    const interval = setInterval(() => {
      setRecordingProgress(prev => {
        const newProgress = prev + (100 / 30) // 30 seconds total
        
        // Simulate heartbeat reading every second
        const simulatedHeartRate = 72 + Math.random() * 10 - 5 // 67-77 bpm range
        setHeartbeatData(prev => [...prev, simulatedHeartRate])

        if (newProgress >= 100) {
          clearInterval(interval)
          setIsRecording(false)
          processEnrollment()
          return 100
        }
        return newProgress
      })
    }, 1000)
  }

  const processEnrollment = async () => {
    setEnrollmentStep('processing')
    
    try {
      // Calculate biometric features
      const meanHR = heartbeatData.reduce((a, b) => a + b, 0) / heartbeatData.length
      const variance = heartbeatData.reduce((sum, hr) => sum + Math.pow(hr - meanHR, 2), 0) / heartbeatData.length
      const stdHR = Math.sqrt(variance)
      const rangeHR = Math.max(...heartbeatData) - Math.min(...heartbeatData)

      // Send to your FastAPI backend
      const enrollmentData = {
        user_id: user?.id,
        heartbeat_pattern: heartbeatData,
        mean_hr: meanHR,
        std_hr: stdHR,
        range_hr: rangeHR,
        device_id: route.params?.deviceId || 'mobile_enrollment',
        enrollment_duration: 30
      }

      // TODO: Replace with actual API call to your Codespace backend
      const response = await fetch('https://obscure-dollop-r4xgv6j6wjvgfp7rp-8000.app.github.dev/api/biometric/enroll', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(enrollmentData)
      })

      if (response.ok) {
        setEnrollmentStep('complete')
      } else {
        throw new Error('Enrollment failed')
      }
    } catch (error) {
      Alert.alert('Enrollment Failed', 'Please try again')
      setEnrollmentStep('intro')
    }
  }

  const renderIntroStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepIcon}>❤️</Text>
      <Text style={styles.stepTitle}>Biometric Enrollment</Text>
      <Text style={styles.stepDescription}>
        We'll record your unique heartbeat pattern for 30 seconds. 
        Please sit comfortably and remain still during the recording.
      </Text>
      <View style={styles.instructions}>
        <Text style={styles.instructionItem}>• Sit in a comfortable position</Text>
        <Text style={styles.instructionItem}>• Keep your device close to your chest</Text>
        <Text style={styles.instructionItem}>• Breathe normally and stay relaxed</Text>
        <Text style={styles.instructionItem}>• The process takes 30 seconds</Text>
      </View>
      <TouchableOpacity style={styles.startButton} onPress={startEnrollment}>
        <Text style={styles.startButtonText}>Start Enrollment</Text>
      </TouchableOpacity>
    </View>
  )

  const renderRecordingStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepIcon}>📊</Text>
      <Text style={styles.stepTitle}>Recording Heartbeat...</Text>
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${recordingProgress}%` }]} />
        </View>
        <Text style={styles.progressText}>{Math.round(recordingProgress)}%</Text>
      </View>
      <Text style={styles.recordingInfo}>
        Samples collected: {heartbeatData.length}
      </Text>
      <Text style={styles.recordingInstruction}>Please remain still...</Text>
    </View>
  )

  const renderProcessingStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepIcon}>⚙️</Text>
      <Text style={styles.stepTitle}>Processing Data...</Text>
      <Text style={styles.stepDescription}>
        Analyzing your heartbeat pattern and creating your biometric profile.
      </Text>
    </View>
  )

  const renderCompleteStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepIcon}>✅</Text>
      <Text style={styles.stepTitle}>Enrollment Complete!</Text>
      <Text style={styles.stepDescription}>
        Your biometric profile has been successfully created. 
        You can now use heartbeat authentication with your devices.
      </Text>
      <TouchableOpacity 
        style={styles.completeButton} 
        onPress={() => navigation.navigate('Dashboard')}
      >
        <Text style={styles.completeButtonText}>Return to Dashboard</Text>
      </TouchableOpacity>
    </View>
  )

  return (
    <View style={styles.container}>
      {enrollmentStep === 'intro' && renderIntroStep()}
      {enrollmentStep === 'recording' && renderRecordingStep()}
      {enrollmentStep === 'processing' && renderProcessingStep()}
      {enrollmentStep === 'complete' && renderCompleteStep()}
    </View>
  )
}

// Placeholder screens for Profile and Device Management
export const ProfileScreen: React.FC<NativeStackScreenProps<MainStackParamList, 'Profile'>> = () => (
  <View style={styles.placeholderContainer}>
    <Text style={styles.placeholderTitle}>Profile Settings</Text>
    <Text style={styles.placeholderText}>Profile management coming soon...</Text>
  </View>
)

export const DeviceManagementScreen: React.FC<NativeStackScreenProps<MainStackParamList, 'DeviceManagement'>> = () => (
  <View style={styles.placeholderContainer}>
    <Text style={styles.placeholderTitle}>Device Management</Text>
    <Text style={styles.placeholderText}>Device pairing coming soon...</Text>
  </View>
)

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  greeting: {
    fontSize: 16,
    color: '#64748b',
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  signOutButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#fee2e2',
    borderRadius: 8,
  },
  signOutText: {
    color: '#dc2626',
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 24,
    paddingVertical: 20,
    gap: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#2563eb',
  },
  statLabel: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 4,
  },
  actionsContainer: {
    paddingHorizontal: 24,
    gap: 12,
  },
  actionCard: {
    backgroundColor: '#ffffff',
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  primaryAction: {
    backgroundColor: '#dbeafe',
    borderColor: '#2563eb',
  },
  actionIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  actionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 4,
  },
  actionDescription: {
    fontSize: 14,
    color: '#64748b',
  },
  activityContainer: {
    paddingHorizontal: 24,
    paddingVertical: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 16,
  },
  activityItem: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  activityIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f1f5f9',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  activityIconText: {
    fontSize: 16,
  },
  activityContent: {
    flex: 1,
  },
  activityDescription: {
    fontSize: 14,
    color: '#1e293b',
    fontWeight: '500',
  },
  activityTime: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  // Enrollment styles
  stepContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  stepIcon: {
    fontSize: 64,
    marginBottom: 24,
  },
  stepTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 16,
    textAlign: 'center',
  },
  stepDescription: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 24,
  },
  instructions: {
    backgroundColor: '#f1f5f9',
    padding: 20,
    borderRadius: 12,
    marginBottom: 32,
    width: '100%',
  },
  instructionItem: {
    fontSize: 14,
    color: '#475569',
    marginBottom: 8,
  },
  startButton: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    width: '100%',
  },
  startButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
  progressContainer: {
    width: '100%',
    marginBottom: 24,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#e2e8f0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#2563eb',
  },
  progressText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2563eb',
    textAlign: 'center',
  },
  recordingInfo: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 8,
  },
  recordingInstruction: {
    fontSize: 16,
    color: '#1e293b',
    fontWeight: '500',
  },
  completeButton: {
    backgroundColor: '#059669',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    width: '100%',
    marginTop: 24,
  },
  completeButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
  placeholderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  placeholderTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 8,
  },
  placeholderText: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
  },
})

export default DashboardScreen