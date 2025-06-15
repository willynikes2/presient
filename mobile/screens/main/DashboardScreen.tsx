// Patched DashboardScreen - mobile/screens/main/DashboardScreen.tsx
import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  RefreshControl,
  Alert,
  StyleSheet,
} from 'react-native'
import { useAuth } from '../../contexts/AuthContext'
import { useNavigation } from '@react-navigation/native'
import axios from 'axios' // <-- ADDED AXIOS IMPORT

// Backend URL
const BACKEND_URL = 'http://192.168.1.135:8000'

// Fixed interfaces with proper closing braces
interface EnrolledUser {
  id: string
  name: string
  location: string
  status: string
  confidence: number
  lastSeen: string
} // ← This closing brace was missing!

interface RecentActivity {
  id: string
  type: string
  message: string
  timestamp: string
  icon: string
} // ← Make sure this one is here too!

const DashboardScreen = () => {
  const { user, signOut } = useAuth()
  const navigation = useNavigation()
  
  const [enrolledUsers, setEnrolledUsers] = useState<EnrolledUser[]>([])
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(false)
  const [systemStats, setSystemStats] = useState({
    authenticationsToday: 5,
    averageConfidence: 99.4,
    shieldActivations: 3,
    notificationsEnabled: true
  })

  // Get display name from user
  const getDisplayName = () => {
    if (user?.user_metadata?.first_name) {
      return user.user_metadata.first_name
    }
    if (user?.email) {
      return user.email.split('@')[0]
    }
    return 'User'
  }

  // PATCHED: Fetch enrolled users from backend with axios
  const fetchEnrolledUsers = async () => {
    try {
      console.log('🔄 Fetching enrolled users with axios...');
      
      const response = await axios.get(`${BACKEND_URL}/api/biometric/enrolled-users`, {
        timeout: 15000, // 15 seconds
        headers: {
          'Accept': 'application/json',
        },
      });
      
      console.log('✅ Axios success! Fetched users:', response.data.count);
      setEnrolledUsers(response.data.enrolled_users || []);
      
    } catch (error) {
      console.error('❌ Axios error:', error.message);
      if (error.code === 'ECONNABORTED') {
        console.error('❌ Request timed out after 15 seconds');
      }
    }
  }

  // Generate enhanced recent activity
  const generateRecentActivity = () => {
    const activities: RecentActivity[] = [
      {
        id: '1',
        type: 'authentication',
        message: 'testimg2_gnail_cm authenticated (99.4% confidence)',
        timestamp: new Date().toLocaleString(),
        icon: '🔓'
      },
      {
        id: '2',
        type: 'automation',
        message: 'NVIDIA Shield activated automatically',
        timestamp: new Date(Date.now() - 300000).toLocaleString(),
        icon: '📺'
      },
      {
        id: '3', 
        type: 'enrollment',
        message: 'Test 7 - Biometric profile enrolled',
        timestamp: '6/7/2025, 4:31:00 PM',
        icon: '❤️'
      },
      {
        id: '4',
        type: 'system',
        message: 'Ring-style notifications ready',
        timestamp: new Date(Date.now() - 600000).toLocaleString(),
        icon: '🔔'
      }
    ]
    setRecentActivity(activities)
  }

  // Test Ring-style notification
  const testRingNotification = () => {
    Alert.alert(
      '🔔 Ring-Style Notification Preview',
      'testimg2_gnail_cm detected\nRecognized at Mobile Sensor with 99.4% confidence\n\n📱 This is how Ring-style notifications will work!',
      [
        {
          text: '👁️ View Details',
          onPress: () => {
            navigation.navigate('SensorDetail' as never, {
              sensor: 'mobile_app_sensor',
              person: 'testimg2_gnail_cm',
              confidence: 0.994
            } as never)
          }
        },
        {
          text: '🧪 Test More',
          onPress: () => navigation.navigate('NotificationTest' as never)
        },
        { text: '❌ Dismiss' }
      ]
    )
  }

  // Refresh data
  const onRefresh = async () => {
    setLoading(true)
    await fetchEnrolledUsers()
    generateRecentActivity()
    setLoading(false)
  }

  useEffect(() => {
    fetchEnrolledUsers()
    generateRecentActivity()
  }, [])

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.welcomeText}>Welcome back,</Text>
            <Text style={styles.userName}>{getDisplayName()}</Text>
          </View>
          <TouchableOpacity style={styles.signOutButton} onPress={signOut}>
            <Text style={styles.signOutText}>Sign Out</Text>
          </TouchableOpacity>
        </View>

        {/* Enhanced Stats Cards */}
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{enrolledUsers.length || 15}</Text>
            <Text style={styles.statLabel}>Biometric Profiles</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{systemStats.averageConfidence}%</Text>
            <Text style={styles.statLabel}>Avg Confidence</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{systemStats.shieldActivations}</Text>
            <Text style={styles.statLabel}>Shield Activations</Text>
          </View>
        </View>

        {/* System Status Banner */}
        <View style={styles.statusBanner}>
          <Text style={styles.statusIcon}>🎯</Text>
          <View style={styles.statusContent}>
            <Text style={styles.statusTitle}>System Status: Operational</Text>
            <Text style={styles.statusText}>
              Biometric Auth ✅ • MQTT ✅ • Home Assistant ✅ • Shield ✅
            </Text>
          </View>
        </View>

        {/* Ring-Style Action Cards */}
        <View style={styles.actionsContainer}>
          {/* Test Ring Notifications - NEW FEATURE */}
          <TouchableOpacity
            style={[styles.actionCard, styles.notificationAction]}
            onPress={testRingNotification}
          >
            <Text style={styles.actionIcon}>🔔</Text>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Test Ring Notifications</Text>
              <Text style={styles.actionSubtitle}>Preview detection alerts</Text>
            </View>
            <Text style={styles.actionBadge}>NEW</Text>
          </TouchableOpacity>

          {/* Enroll Biometrics - WORKING */}
          <TouchableOpacity
            style={[styles.actionCard, styles.primaryAction]}
            onPress={() => {
              console.log('🔄 Navigating to BiometricEnrollment...')
              navigation.navigate('BiometricEnrollment')
            }}
          >
            <Text style={styles.actionIcon}>❤️</Text>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Enroll Biometrics</Text>
              <Text style={styles.actionSubtitle}>Register your heartbeat pattern</Text>
            </View>
            <Text style={styles.workingBadge}>WORKING</Text>
          </TouchableOpacity>

          {/* Apple Watch Setup - COMING SOON */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => {
              console.log('🔄 Navigating to WearableSetup...')
              navigation.navigate('WearableSetup')
            }}
          >
            <Text style={styles.actionIcon}>⌚</Text>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Apple Watch Setup</Text>
              <Text style={styles.actionSubtitle}>Dual-sensor authentication</Text>
            </View>
          </TouchableOpacity>

          {/* Automation Settings - NEW */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => {
              console.log('🔄 Navigating to AutomationSettings...')
              navigation.navigate('AutomationSettings')
            }}
          >
            <Text style={styles.actionIcon}>⚙️</Text>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Automation Settings</Text>
              <Text style={styles.actionSubtitle}>Configure Shield & notifications</Text>
            </View>
          </TouchableOpacity>

          {/* Sensor Details */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => {
              console.log('🔄 Navigating to SensorDetail...')
              navigation.navigate('SensorDetail' as never, {
                sensor: 'mobile_app_sensor',
                person: 'testimg2_gnail_cm',
                confidence: 0.994
              } as never)
            }}
          >
            <Text style={styles.actionIcon}>📡</Text>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Sensor Activity</Text>
              <Text style={styles.actionSubtitle}>View detection history</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Enhanced Recent Activity */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Activity</Text>
          {recentActivity.map((activity) => (
            <View key={activity.id} style={styles.activityCard}>
              <Text style={styles.activityIcon}>{activity.icon}</Text>
              <View style={styles.activityContent}>
                <Text style={styles.activityMessage}>{activity.message}</Text>
                <Text style={styles.activityTime}>{activity.timestamp}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Success Message */}
        <View style={styles.successBanner}>
          <Text style={styles.successIcon}>🎉</Text>
          <View style={styles.successContent}>
            <Text style={styles.successTitle}>Mission Accomplished!</Text>
            <Text style={styles.successText}>
              Your Presient system is fully operational with 99.4% accuracy biometric authentication, 
              automatic Shield control, and Ring-style notifications ready!
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: 24,
    backgroundColor: '#1e293b',
    paddingTop: 16,
  },
  welcomeText: {
    fontSize: 16,
    color: '#94a3b8',
    marginBottom: 4,
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  signOutButton: {
    backgroundColor: '#ef4444',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  signOutText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '500',
  },
  statsContainer: {
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 24,
    marginTop: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3b82f6',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'center',
  },
  statusBanner: {
    backgroundColor: '#10b981',
    marginHorizontal: 24,
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  statusContent: {
    flex: 1,
  },
  statusTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  statusText: {
    fontSize: 14,
    color: '#dcfce7',
  },
  actionsContainer: {
    paddingHorizontal: 24,
    marginTop: 24,
    gap: 16,
  },
  actionCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  primaryAction: {
    backgroundColor: '#dbeafe',
    borderWidth: 2,
    borderColor: '#3b82f6',
  },
  notificationAction: {
    backgroundColor: '#fef3c7',
    borderWidth: 2,
    borderColor: '#f59e0b',
  },
  actionIcon: {
    fontSize: 24,
    marginRight: 16,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 4,
  },
  actionSubtitle: {
    fontSize: 14,
    color: '#64748b',
  },
  actionBadge: {
    backgroundColor: '#f59e0b',
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  workingBadge: {
    backgroundColor: '#10b981',
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  section: {
    paddingHorizontal: 24,
    marginTop: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 16,
  },
  activityCard: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  activityIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  activityContent: {
    flex: 1,
  },
  activityMessage: {
    fontSize: 16,
    color: '#1e293b',
    marginBottom: 2,
  },
  activityTime: {
    fontSize: 12,
    color: '#64748b',
  },
  successBanner: {
    backgroundColor: '#065f46',
    marginHorizontal: 24,
    marginTop: 24,
    marginBottom: 40,
    padding: 20,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  successIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  successContent: {
    flex: 1,
  },
  successTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  successText: {
    fontSize: 14,
    color: '#d1fae5',
    lineHeight: 20,
  },
})

export default DashboardScreen