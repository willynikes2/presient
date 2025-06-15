// Sensor Detail Screen - Ring-Style Navigation Target
// mobile/screens/main/SensorDetailScreen.tsx

import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  ActivityIndicator,
  RefreshControl,
  Alert
} from 'react-native'
import { useNavigation, useRoute } from '@react-navigation/native'
import { useAuth } from '../../contexts/AuthContext'

interface SensorEvent {
  id: string
  person: string
  confidence: number
  timestamp: string
  sensor_id: string
  device_type: string
  source: string
  location?: string
  heart_rate?: number
  heart_rate_wearable?: number
  breathing_rate?: number
}

interface SensorInfo {
  id: string
  name: string
  type: string
  location: string
  status: 'online' | 'offline' | 'warning'
  last_seen: string
  total_detections: number
  accuracy_rate: number
}

const SensorDetailScreen = () => {
  const navigation = useNavigation()
  const route = useRoute()
  const { user } = useAuth()
  
  // Get sensor ID from navigation params (from notification tap)
  const sensorId = (route.params as any)?.sensor || 'mobile_app_sensor'
  
  const [sensorInfo, setSensorInfo] = useState<SensorInfo | null>(null)
  const [recentEvents, setRecentEvents] = useState<SensorEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const BACKEND_URL = 'http://192.168.1.135:8000'

  useEffect(() => {
    loadSensorData()
  }, [sensorId])

  const loadSensorData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setIsRefreshing(true)
      } else {
        setIsLoading(true)
      }
      
      console.log(`📊 Loading sensor data for: ${sensorId}`)
      
      // Load sensor info and recent events
      await Promise.all([
        loadSensorInfo(),
        loadRecentEvents()
      ])
      
    } catch (error) {
      console.error('❌ Error loading sensor data:', error)
      Alert.alert(
        'Error',
        'Failed to load sensor data. Please try again.',
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const loadSensorInfo = async () => {
    try {
      // For now, simulate sensor info since backend endpoint may not exist yet
      const mockSensorInfo: SensorInfo = {
        id: sensorId,
        name: getSensorDisplayName(sensorId),
        type: sensorId === 'mobile_app_sensor' ? 'Mobile Biometric' : 'mmWave Sensor',
        location: sensorId === 'mobile_app_sensor' ? 'Mobile Device' : 'Entry Point',
        status: 'online',
        last_seen: new Date().toISOString(),
        total_detections: 47,
        accuracy_rate: 94.8
      }
      
      setSensorInfo(mockSensorInfo)
      console.log('✅ Sensor info loaded:', mockSensorInfo)
      
    } catch (error) {
      console.error('❌ Error loading sensor info:', error)
    }
  }

  const loadRecentEvents = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/sensors/${sensorId}/events?limit=10`)
      
      if (response.ok) {
        const events = await response.json()
        setRecentEvents(events)
        console.log(`✅ Loaded ${events.length} recent events`)
      } else {
        // Mock recent events if endpoint doesn't exist
        const mockEvents: SensorEvent[] = [
          {
            id: '1',
            person: 'testimg2_gnail_cm',
            confidence: 99.4,
            timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
            sensor_id: sensorId,
            device_type: 'mobile',
            source: 'dual_sensor',
            location: 'Living Room',
            heart_rate: 76.6,
            heart_rate_wearable: 74,
            breathing_rate: 16
          },
          {
            id: '2',
            person: 'teesting_hmali_com',
            confidence: 87.3,
            timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
            sensor_id: sensorId,
            device_type: 'mobile',
            source: 'phone_only',
            location: 'Kitchen',
            heart_rate: 87.37,
            breathing_rate: 16
          },
          {
            id: '3',
            person: 'unknown_person',
            confidence: 45.2,
            timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
            sensor_id: sensorId,
            device_type: 'mobile',
            source: 'phone_only',
            location: 'Front Door',
            heart_rate: 82.1,
            breathing_rate: 18
          }
        ]
        
        setRecentEvents(mockEvents)
        console.log('✅ Loaded mock recent events')
      }
      
    } catch (error) {
      console.error('❌ Error loading recent events:', error)
    }
  }

  const getSensorDisplayName = (sensorId: string): string => {
    switch (sensorId) {
      case 'mobile_app_sensor':
        return '📱 Mobile Biometric Sensor'
      case 'entryway_1':
        return '🚪 Front Door Sensor'
      case 'living_room_1':
        return '🛋️ Living Room Sensor'
      default:
        return `📡 ${sensorId}`
    }
  }

  const getPersonDisplayName = (person: string): string => {
    return person.replace(/_/g, ' ').replace(/gmail com|hmali com/g, '').trim() || person
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return '#10b981'
      case 'warning':
        return '#f59e0b'
      case 'offline':
        return '#ef4444'
      default:
        return '#64748b'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return '#10b981'
    if (confidence >= 70) return '#f59e0b'
    return '#ef4444'
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMins / 60)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return date.toLocaleDateString()
  }

  const testSensorConnection = async () => {
    try {
      console.log(`🧪 Testing connection to sensor: ${sensorId}`)
      
      Alert.alert(
        '🧪 Sensor Test',
        `Testing connection to ${sensorInfo?.name}...\n\nThis would ping the sensor and verify connectivity.`,
        [{ text: 'OK' }],
        { userInterfaceStyle: 'dark' }
      )
      
    } catch (error) {
      console.error('❌ Sensor test error:', error)
    }
  }

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#10B981" />
          <Text style={styles.loadingText}>Loading sensor data...</Text>
        </View>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        style={styles.content} 
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={() => loadSensorData(true)}
            tintColor="#10B981"
          />
        }
      >
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Sensor Details</Text>
          <View style={styles.placeholder} />
        </View>

        {/* Sensor Info Card */}
        {sensorInfo && (
          <View style={styles.sensorCard}>
            <View style={styles.sensorHeader}>
              <View style={styles.sensorTitleContainer}>
                <Text style={styles.sensorName}>{sensorInfo.name}</Text>
                <View style={[styles.statusBadge, { backgroundColor: getStatusColor(sensorInfo.status) }]}>
                  <Text style={styles.statusText}>{sensorInfo.status.toUpperCase()}</Text>
                </View>
              </View>
              <Text style={styles.sensorLocation}>📍 {sensorInfo.location}</Text>
            </View>
            
            <View style={styles.sensorStats}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{sensorInfo.total_detections}</Text>
                <Text style={styles.statLabel}>Total Detections</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{sensorInfo.accuracy_rate}%</Text>
                <Text style={styles.statLabel}>Accuracy Rate</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{formatTimestamp(sensorInfo.last_seen)}</Text>
                <Text style={styles.statLabel}>Last Seen</Text>
              </View>
            </View>
            
            <TouchableOpacity style={styles.testButton} onPress={testSensorConnection}>
              <Text style={styles.testButtonText}>🧪 Test Connection</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Recent Events */}
        <View style={styles.eventsSection}>
          <Text style={styles.eventsTitle}>📋 Recent Detection Events</Text>
          
          {recentEvents.length === 0 ? (
            <View style={styles.noEventsContainer}>
              <Text style={styles.noEventsText}>No recent events</Text>
              <Text style={styles.noEventsSubtext}>Events will appear here when people are detected</Text>
            </View>
          ) : (
            <View style={styles.eventsList}>
              {recentEvents.map((event) => (
                <View key={event.id} style={styles.eventCard}>
                  <View style={styles.eventHeader}>
                    <View style={styles.eventTitleContainer}>
                      <Text style={styles.eventPerson}>
                        👤 {getPersonDisplayName(event.person)}
                      </Text>
                      <View style={[
                        styles.confidenceBadge, 
                        { backgroundColor: getConfidenceColor(event.confidence) }
                      ]}>
                        <Text style={styles.confidenceText}>
                          {event.confidence.toFixed(1)}%
                        </Text>
                      </View>
                    </View>
                    <Text style={styles.eventTimestamp}>
                      🕐 {formatTimestamp(event.timestamp)}
                    </Text>
                  </View>
                  
                  <View style={styles.eventDetails}>
                    <Text style={styles.eventDetail}>📡 Source: {event.source.replace('_', ' + ')}</Text>
                    {event.location && (
                      <Text style={styles.eventDetail}>📍 Location: {event.location}</Text>
                    )}
                    {event.heart_rate && (
                      <Text style={styles.eventDetail}>💓 Heart Rate: {event.heart_rate} BPM</Text>
                    )}
                    {event.heart_rate_wearable && (
                      <Text style={styles.eventDetail}>⌚ Watch HR: {event.heart_rate_wearable} BPM</Text>
                    )}
                    {event.breathing_rate && (
                      <Text style={styles.eventDetail}>🫁 Breathing: {event.breathing_rate} BPM</Text>
                    )}
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>

        {/* Actions */}
        <View style={styles.actionsSection}>
          <TouchableOpacity 
            style={styles.actionButton} 
            onPress={() => navigation.navigate('AutomationSettings' as never)}
          >
            <Text style={styles.actionButtonText}>⚙️ Automation Settings</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionButton} 
            onPress={() => loadSensorData(true)}
          >
            <Text style={styles.actionButtonText}>🔄 Refresh Data</Text>
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
  sensorCard: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  sensorHeader: {
    marginBottom: 16,
  },
  sensorTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  sensorName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  sensorLocation: {
    fontSize: 14,
    color: '#94a3b8',
  },
  sensorStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#10b981',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#94a3b8',
    textAlign: 'center',
  },
  testButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  testButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  eventsSection: {
    marginBottom: 20,
  },
  eventsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
  },
  noEventsContainer: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
  },
  noEventsText: {
    fontSize: 16,
    color: '#94a3b8',
    marginBottom: 8,
  },
  noEventsSubtext: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
  },
  eventsList: {
    gap: 12,
  },
  eventCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
  },
  eventHeader: {
    marginBottom: 12,
  },
  eventTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  eventPerson: {
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
  eventTimestamp: {
    fontSize: 14,
    color: '#94a3b8',
  },
  eventDetails: {
    gap: 4,
  },
  eventDetail: {
    fontSize: 14,
    color: '#94a3b8',
  },
  actionsSection: {
    gap: 12,
    marginBottom: 20,
  },
  actionButton: {
    backgroundColor: '#374151',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
})

export default SensorDetailScreen