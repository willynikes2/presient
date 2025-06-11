// screens/main/SensorDetailScreen.tsx - Ring-Style Notification Target
import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native'
import { useRoute, useNavigation } from '@react-navigation/native'

interface RouteParams {
  sensor: string
  person?: string
  confidence?: number
}

interface ActivityItem {
  id: string
  person: string
  timestamp: string
  confidence: number
  sensor: string
  source: 'sensor_only' | 'watch_only' | 'sensor+watch'
}

export default function SensorDetailScreen() {
  const route = useRoute()
  const navigation = useNavigation()
  const params = route.params as RouteParams
  
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [sensorStatus, setSensorStatus] = useState<'online' | 'offline' | 'error'>('online')

  useEffect(() => {
    loadSensorData()
  }, [params.sensor])

  const loadSensorData = async () => {
    try {
      console.log(`📡 Loading data for sensor: ${params.sensor}`)
      
      // TODO: Fetch real sensor data from backend
      // const response = await fetch(`/api/sensors/${params.sensor}/activity`)
      // const data = await response.json()
      
      // Mock data for now
      const mockActivities: ActivityItem[] = [
        {
          id: '1',
          person: params.person || 'testimg2_gnail_cm',
          timestamp: new Date().toISOString(),
          confidence: params.confidence || 0.991,
          sensor: params.sensor,
          source: 'sensor+watch'
        },
        {
          id: '2',
          person: 'capitalisandme_gmail_com',
          timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
          confidence: 0.943,
          sensor: params.sensor,
          source: 'sensor_only'
        },
        {
          id: '3',
          person: 'jane_smith',
          timestamp: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
          confidence: 0.887,
          sensor: params.sensor,
          source: 'watch_only'
        },
      ]
      
      setActivities(mockActivities)
      setSensorStatus('online')
      
    } catch (error) {
      console.error('❌ Error loading sensor data:', error)
      setSensorStatus('error')
    }
  }

  const onRefresh = async () => {
    setIsRefreshing(true)
    await loadSensorData()
    setIsRefreshing(false)
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return date.toLocaleDateString()
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.95) return '#10b981' // green
    if (confidence >= 0.85) return '#f59e0b' // yellow
    return '#ef4444' // red
  }

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'sensor+watch': return '📱⌚'
      case 'watch_only': return '⌚'
      case 'sensor_only': return '📱'
      default: return '❓'
    }
  }

  const getSensorIcon = (sensorName: string) => {
    if (sensorName.includes('mobile')) return '📱'
    if (sensorName.includes('front')) return '🚪'
    if (sensorName.includes('back')) return '🏠'
    if (sensorName.includes('garage')) return '🚗'
    return '📡'
  }

  const handleTestNotification = () => {
    Alert.alert(
      'Test Notification',
      `This would send a test Ring-style notification for ${params.sensor}`,
      [{ text: 'OK' }]
    )
  }

  const renderSensorHeader = () => (
    <View style={styles.headerContainer}>
      <View style={styles.sensorInfo}>
        <Text style={styles.sensorIcon}>{getSensorIcon(params.sensor)}</Text>
        <View style={styles.sensorDetails}>
          <Text style={styles.sensorName}>{params.sensor.replace(/_/g, ' ')}</Text>
          <View style={styles.statusContainer}>
            <View style={[styles.statusDot, { backgroundColor: sensorStatus === 'online' ? '#10b981' : '#ef4444' }]} />
            <Text style={styles.statusText}>{sensorStatus === 'online' ? 'Online' : 'Offline'}</Text>
          </View>
        </View>
      </View>
      
      <TouchableOpacity style={styles.testButton} onPress={handleTestNotification}>
        <Text style={styles.testButtonText}>🧪 Test</Text>
      </TouchableOpacity>
    </View>
  )

  const renderActivity = (activity: ActivityItem) => (
    <View key={activity.id} style={styles.activityItem}>
      <View style={styles.activityHeader}>
        <View style={styles.activityInfo}>
          <Text style={styles.activityPerson}>{activity.person}</Text>
          <Text style={styles.activityTime}>{formatTimestamp(activity.timestamp)}</Text>
        </View>
        <View style={styles.activityMeta}>
          <Text style={styles.sourceIcon}>{getSourceIcon(activity.source)}</Text>
          <Text style={[styles.confidence, { color: getConfidenceColor(activity.confidence) }]}>
            {Math.round(activity.confidence * 100)}%
          </Text>
        </View>
      </View>
      
      <View style={styles.activityDetails}>
        <Text style={styles.activitySource}>
          Source: {activity.source.replace('+', ' + ').replace('_', ' ')}
        </Text>
      </View>
    </View>
  )

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={isRefreshing}
          onRefresh={onRefresh}
          tintColor="#3b82f6"
        />
      }
    >
      {renderSensorHeader()}
      
      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{activities.length}</Text>
          <Text style={styles.statLabel}>Detections Today</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>99.1%</Text>
          <Text style={styles.statLabel}>Avg Confidence</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>3</Text>
          <Text style={styles.statLabel}>Unique People</Text>
        </View>
      </View>
      
      <View style={styles.sectionContainer}>
        <Text style={styles.sectionTitle}>Recent Activity</Text>
        {activities.length > 0 ? (
          activities.map(renderActivity)
        ) : (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No recent activity</Text>
            <Text style={styles.emptySubtext}>Detections will appear here</Text>
          </View>
        )}
      </View>
      
      <TouchableOpacity 
        style={styles.settingsButton}
        onPress={() => navigation.navigate('AutomationSettings' as never)}
      >
        <Text style={styles.settingsButtonText}>⚙️ Automation Settings</Text>
      </TouchableOpacity>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  headerContainer: {
    backgroundColor: '#1e293b',
    padding: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sensorInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  sensorIcon: {
    fontSize: 32,
    marginRight: 16,
  },
  sensorDetails: {
    flex: 1,
  },
  sensorName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
    textTransform: 'capitalize',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  statusText: {
    fontSize: 14,
    color: '#94a3b8',
  },
  testButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  testButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#1e293b',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  statLabel: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 4,
    textAlign: 'center',
  },
  sectionContainer: {
    margin: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
  },
  activityItem: {
    backgroundColor: '#1e293b',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  activityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  activityInfo: {
    flex: 1,
  },
  activityPerson: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  activityTime: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 2,
  },
  activityMeta: {
    alignItems: 'flex-end',
  },
  sourceIcon: {
    fontSize: 16,
    marginBottom: 4,
  },
  confidence: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  activityDetails: {
    marginTop: 8,
  },
  activitySource: {
    fontSize: 12,
    color: '#64748b',
    textTransform: 'capitalize',
  },
  emptyContainer: {
    backgroundColor: '#1e293b',
    padding: 40,
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#94a3b8',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#64748b',
  },
  settingsButton: {
    backgroundColor: '#374151',
    margin: 20,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  settingsButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
})