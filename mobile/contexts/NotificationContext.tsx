// contexts/NotificationContext.tsx - Ring-Style Notification System
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import * as Notifications from 'expo-notifications'
import * as Device from 'expo-device'
import AsyncStorage from '@react-native-async-storage/async-storage'

// Configure notifications to show in foreground (Ring-style)
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
  notificationsEnabled: boolean
  isSetup: boolean
  sendTestNotification: () => Promise<void>
  enableNotifications: () => Promise<boolean>
  disableNotifications: () => Promise<void>
  sendDetectionNotification: (person: string, sensor: string, confidence: number) => Promise<void>
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export const useNotifications = () => {
  const context = useContext(NotificationContext)
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}

interface NotificationProviderProps {
  children: ReactNode
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null)
  const [notificationsEnabled, setNotificationsEnabled] = useState(false)
  const [isSetup, setIsSetup] = useState(false)

  useEffect(() => {
    setupNotifications()
    setupNotificationListeners()
  }, [])

  const setupNotifications = async () => {
    try {
      console.log('🔧 Setting up Ring-style notifications...')
      
      // Check if notifications are enabled in settings
      const enabled = await AsyncStorage.getItem('notifications_enabled')
      setNotificationsEnabled(enabled === 'true')

      if (!Device.isDevice) {
        console.log('⚠️ Push notifications only work on physical devices')
        setIsSetup(true)
        return
      }

      // Get existing permissions
      const { status: existingStatus } = await Notifications.getPermissionsAsync()
      
      if (existingStatus === 'granted') {
        await setupPushToken()
      }
      
      setIsSetup(true)
      console.log('🎉 Ring-style notifications setup complete!')
      
    } catch (error) {
      console.error('❌ Notification setup error:', error)
      setIsSetup(true)
    }
  }

  const setupPushToken = async () => {
    try {
      const token = await Notifications.getExpoPushTokenAsync({
        projectId: 'presient-app'
      })
      
      setExpoPushToken(token.data)
      console.log('✅ Push token obtained:', token.data)
      
      // TODO: Send token to backend for storage
      // await sendTokenToBackend(token.data)
      
    } catch (error) {
      console.error('❌ Push token error:', error)
    }
  }

  const setupNotificationListeners = () => {
    // Listen for notifications when app is open
    const notificationListener = Notifications.addNotificationReceivedListener(notification => {
      console.log('🔔 Ring-style notification received:', notification)
    })

    // Listen for notification taps (Ring-style navigation)
    const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
      console.log('📱 Notification tapped:', response)
      
      const data = response.notification.request.content.data
      if (data?.sensor) {
        // Log navigation intent - actual navigation will be handled by the app
        console.log('🔄 Should navigate to sensor:', data.sensor, 'person:', data.person)
        // TODO: Use a different navigation approach or event system
      }
    })

    return () => {
      Notifications.removeNotificationSubscription(notificationListener)
      Notifications.removeNotificationSubscription(responseListener)
    }
  }

  const enableNotifications = async (): Promise<boolean> => {
    try {
      if (!Device.isDevice) {
        console.log('⚠️ Push notifications only work on physical devices')
        return false
      }

      console.log('🔑 Requesting notification permissions...')
      const { status } = await Notifications.requestPermissionsAsync()
      
      if (status !== 'granted') {
        console.log('❌ Notification permissions denied')
        return false
      }

      await setupPushToken()
      setNotificationsEnabled(true)
      await AsyncStorage.setItem('notifications_enabled', 'true')
      
      console.log('✅ Ring-style notifications enabled!')
      return true
      
    } catch (error) {
      console.error('❌ Enable notifications error:', error)
      return false
    }
  }

  const disableNotifications = async () => {
    try {
      setNotificationsEnabled(false)
      await AsyncStorage.setItem('notifications_enabled', 'false')
      console.log('🔕 Ring-style notifications disabled')
    } catch (error) {
      console.error('❌ Disable notifications error:', error)
    }
  }

  const sendTestNotification = async () => {
    try {
      if (!notificationsEnabled) {
        console.log('⚠️ Notifications not enabled')
        return
      }

      await Notifications.scheduleNotificationAsync({
        content: {
          title: '🔍 testimg2_gnail_cm detected',
          body: 'Recognized at Mobile Sensor with 99.1% confidence',
          data: { 
            person: 'testimg2_gnail_cm',
            sensor: 'mobile_app_sensor',
            confidence: 0.991,
            timestamp: new Date().toISOString()
          },
        },
        trigger: { seconds: 2 },
      })
      
      console.log('📨 Ring-style test notification sent')
    } catch (error) {
      console.error('❌ Test notification error:', error)
    }
  }

  const sendDetectionNotification = async (person: string, sensor: string, confidence: number) => {
    try {
      if (!notificationsEnabled) {
        return
      }

      const confidencePercent = Math.round(confidence * 100)
      
      await Notifications.scheduleNotificationAsync({
        content: {
          title: `🔍 ${person} detected`,
          body: `Recognized at ${sensor} with ${confidencePercent}% confidence`,
          data: { 
            person,
            sensor,
            confidence,
            timestamp: new Date().toISOString()
          },
        },
        trigger: { seconds: 1 },
      })
      
      console.log(`📨 Ring-style detection notification sent for ${person}`)
    } catch (error) {
      console.error('❌ Detection notification error:', error)
    }
  }

  return (
    <NotificationContext.Provider
      value={{
        expoPushToken,
        notificationsEnabled,
        isSetup,
        sendTestNotification,
        enableNotifications,
        disableNotifications,
        sendDetectionNotification,
      }}
    >
      {children}
    </NotificationContext.Provider>
  )
}