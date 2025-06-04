// Patched DashboardScreen - mobile/screens/main/DashboardScreen.tsx
// Real navigation to BiometricEnrollmentScreen (no more "Coming Soon")

import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  RefreshControl,
} from 'react-native'
import { useAuth } from '../../contexts/AuthContext'
import { useNavigation } from '@react-navigation/native'

// Backend URL
const BACKEND_URL = 'http://192.168.1.135:8000'

interface EnrolledUser {
  id: string
  name: string
  location: string
  status: string
  confidence: number
  lastSeen: string
}

interface RecentActivity {
  id: string
  type: string
  message: string
  timestamp: string
  icon: string
}

const DashboardScreen = () => {
  const { user, signOut } = useAuth()
  const navigation = useNavigation()
  
  const [enrolledUsers, setEnrolledUsers] = useState<EnrolledUser[]>([])
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(false)

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

  // Fetch enrolled users from backend
  const fetchEnrolledUsers = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/biometric/enrolled-users`)
      const data = await response.json()
      
      if (response.ok) {
        setEnrolledUsers(data.enrolled_users || [])
        console.log('✅ Fetched enrolled users:', data.enrolled_users?.length || 0)
      }
    } catch (error) {
      console.error('❌ Failed to fetch enrolled users:', error)
    }
  }

  // Generate recent activity (mock data for now)
  const generateRecentActivity = () => {
    const activities: RecentActivity[] = [
      {
        id: '1',
        type: 'authentication',
        message: 'Successfully authenticated via princeton_mmwave',
        timestamp: '6/2/2025, 1:16:18 PM',
        icon: '🔓'
      },
      {
        id: '2', 
        type: 'enrollment',
        message: 'Biometric profile enrolled',
        timestamp: '6/2/2025, 12:24:01 PM',
        icon: '❤️'
      }
    ]
    setRecentActivity(activities)
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

        {/* Stats Cards */}
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>1</Text>
            <Text style={styles.statLabel}>Enrolled Devices</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{enrolledUsers.length}</Text>
            <Text style={styles.statLabel}>Biometric Profiles</Text>
          </View>
        </View>

        {/* Action Cards */}
        <View style={styles.actionsContainer}>
          {/* Enroll Biometrics - REAL NAVIGATION */}
          <TouchableOpacity
            style={[styles.actionCard, styles.primaryAction]}
            onPress={() => {
              console.log('🔄 Navigating to BiometricEnrollment...')
              navigation.navigate('BiometricEnrollment' as never)
            }}
          >
            <Text style={styles.actionIcon}>❤️</Text>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Enroll Biometrics</Text>
              <Text style={styles.actionSubtitle}>Register your heartbeat pattern</Text>
            </View>
          </TouchableOpacity>

          {/* Manage Devices - Placeholder for now */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => {
              console.log('🔄 Navigating to DeviceManagement...')
              navigation.navigate('DeviceManagement' as never)
            }}
          >
            <Text style={styles.actionIcon}>📱</Text>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Manage Devices</Text>
              <Text style={styles.actionSubtitle}>Add or configure sensors</Text>
            </View>
          </TouchableOpacity>

          {/* Profile Settings - Placeholder for now */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => {
              console.log('🔄 Navigating to Profile...')
              navigation.navigate('Profile' as never)
            }}
          >
            <Text style={styles.actionIcon}>👤</Text>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Profile Settings</Text>
              <Text style={styles.actionSubtitle}>Update your information</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Enrolled Users Section */}
        {enrolledUsers.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Enrolled Family Members</Text>
            {enrolledUsers.map((user) => (
              <View key={user.id} style={styles.userCard}>
                <View style={styles.userInfo}>
                  <Text style={styles.userCardName}>{user.name}</Text>
                  <Text style={styles.userLocation}>{user.location}</Text>
                </View>
                <View style={styles.userStatus}>
                  <Text style={styles.statusText}>{user.status}</Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Recent Activity */}
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
    gap: 16,
    paddingHorizontal: 24,
    marginTop: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#3b82f6',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
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
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  primaryAction: {
    backgroundColor: '#dbeafe',
    borderWidth: 2,
    borderColor: '#3b82f6',
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
  userCard: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  userInfo: {
    flex: 1,
  },
  userCardName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  userLocation: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 2,
  },
  userStatus: {
    backgroundColor: '#10b981',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '500',
  },
  activityCard: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
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
})

export default DashboardScreen
