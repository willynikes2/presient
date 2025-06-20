// Real Push Notification System - Build Note 2
// mobile/contexts/NotificationContext.tsx

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { Platform, Alert } from 'react-native'
import * as Notifications from 'expo-notifications'
import * as Device from 'expo-device'
import { useAuth } from './AuthContext'

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
})

interface NotificationContextType {
  expoPushToken: string | null
  isNotificationEnabled: boolean
  setupNotifications: () => Promise<boolean>
  sendTestNotification: () => Promise<void>
  sendPresenceNotification: (person: string, sensor: string, confidence: number) => Promise<void>
}

interface PresenceNotificationData {
  person: string
  sensor: string
  confidence: number
  timestamp: string
  type: 'presence_detection'
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export const useNotifications = () => {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return context
}

interface NotificationProviderProps {
  children: ReactNode
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const { user } = useAuth()
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null)
  const [isNotificationEnabled, setIsNotificationEnabled] = useState(false)

  // Setup notifications on app start
  useEffect(() => {
    if (user) {
      setupNotifications()
    }
  }, [user])

  // Listen for notification taps
  useEffect(() => {
    // Handle notification tap when app is in foreground
    const foregroundSubscription = Notifications.addNotificationReceivedListener(notification => {
      console.log('📱 Notification received in foreground:', notification)
    })

    // Handle notification tap when app is in background
    const backgroundSubscription = Notifications.addNotificationResponseReceivedListener(response => {
      console.log('👆 Notification tapped:', response)
      
      const data = response.notification.request.content.data as unknown as PresenceNotificationData
      if (data && data.type === 'presence_detection') {
        // Navigate to sensor detail screen
        // This will be implemented when we add navigation
        console.log(`🔍 Should navigate to sensor detail: ${data.sensor}`)
        console.log(`👤 Person: ${data.person}, Confidence: ${data.confidence}%`)
      }
    })

    return () => {
      foregroundSubscription.remove()
      backgroundSubscription.remove()
    }
  }, [])

  const setupNotifications = async (): Promise<boolean> => {
    try {
      console.log('🔔 Setting up Ring-style notifications...')

      // Check if running on physical device
      if (!Device.isDevice) {
        Alert.alert('Info', 'Push notifications only work on physical devices')
        return false
      }

      // Request permissions
      const { status: existingStatus } = await Notifications.getPermissionsAsync()
      let finalStatus = existingStatus
      
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync()
        finalStatus = status
      }
      
      if (finalStatus !== 'granted') {
        Alert.alert('Error', 'Push notification permissions are required for Ring-style alerts')
        return false
      }

      // Get push token
      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId: '47c2bb5c-0d82-4c73-8d87-0669bf17cfe9' // Replace with your actual project ID
      })
      
      const token = tokenData.data
      console.log('✅ Expo push token generated:', token)
      
      setExpoPushToken(token)
      setIsNotificationEnabled(true)

      // Save token to your backend/Supabase
      if (user && token) {
        await savePushTokenToBackend(token)
      }

      console.log('🔔 Ring-style notifications setup complete!')
      return true

    } catch (error) {
      console.error('❌ Notification setup error:', error)
      Alert.alert('Error', 'Failed to setup notifications. Please try again.')
      return false
    }
  }

  const savePushTokenToBackend = async (token: string) => {
    try {
      console.log('💾 Saving push token to backend...')
      
      // Save to your FastAPI backend
      const response = await fetch('https://orange-za-speech-dosage.trycloudflare.com/api/notifications/register-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.email?.replace(/[@.]/g, '_') || 'unknown_user',
          push_token: token,
          device_type: Platform.OS,
          device_id: Device.modelId || 'unknown_device'
        })
      })

      if (response.ok) {
        console.log('✅ Push token saved to backend')
      } else {
        console.error('❌ Failed to save push token to backend')
      }
    } catch (error) {
      console.error('❌ Error saving push token:', error)
    }
  }

  const sendTestNotification = async () => {
    try {
      if (!expoPushToken) {
        Alert.alert('Error', 'No push token available. Please setup notifications first.')
        return
      }

      console.log('🧪 Sending test Ring-style notification...')

      // Schedule local notification for immediate testing
      await Notifications.scheduleNotificationAsync({
        content: {
          title: '🏠 Test User detected',
          body: 'Recognized at Mobile Sensor with 95.0% confidence',
          data: {
            person: 'test_user',
            sensor: 'mobile_app_sensor', 
            confidence: 95.0,
            timestamp: new Date().toISOString(),
            type: 'presence_detection'
          } as PresenceNotificationData,
        },
        trigger: { seconds: 2 },
      })

      Alert.alert('🔔 Test Notification Sent!', 'Check your notification tray in 2 seconds')

    } catch (error) {
      console.error('❌ Test notification error:', error)
      Alert.alert('Error', 'Failed to send test notification')
    }
  }

  const sendPresenceNotification = async (person: string, sensor: string, confidence: number) => {
    try {
      if (!expoPushToken || !isNotificationEnabled) {
        console.log('⚠️ Notifications not enabled, skipping')
        return
      }

      console.log(`🔔 Sending Ring-style notification: ${person} detected`)

      // Send via Expo push service (for real push notifications)
      const message = {
        to: expoPushToken,
        title: `🏠 ${person} detected`,
        body: `Recognized at ${sensor} with ${confidence.toFixed(1)}% confidence`,
        data: {
          person,
          sensor,
          confidence,
          timestamp: new Date().toISOString(),
          type: 'presence_detection'
        } as PresenceNotificationData,
        sound: 'default',
        badge: 1,
      }

      // Send to Expo push service
      const response = await fetch('https://exp.host/--/api/v2/push/send', {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Accept-encoding': 'gzip, deflate',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(message),
      })

      const result = await response.json()
      console.log('📡 Push notification sent:', result)

    } catch (error) {
      console.error('❌ Presence notification error:', error)
    }
  }

  return (
    <NotificationContext.Provider
      value={{
        expoPushToken,
        isNotificationEnabled,
        setupNotifications,
        sendTestNotification,
        sendPresenceNotification,
      }}
    >
      {children}
    </NotificationContext.Provider>
  )
}