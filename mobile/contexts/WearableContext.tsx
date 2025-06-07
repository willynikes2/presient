// contexts/WearableContext.tsx - Apple Watch Heart Rate Integration
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import AsyncStorage from '@react-native-async-storage/async-storage'
import * as Device from 'expo-device'
import { Platform } from 'react-native'

// Note: react-native-health will be installed separately
// import { HealthKit } from 'react-native-health'

interface WearableData {
  heartRate: number
  timestamp: string
  source: 'apple_watch' | 'unknown'
}

interface WearableContextType {
  hasWearable: boolean
  isWearableConnected: boolean
  isSetup: boolean
  wearableType: 'apple_watch' | 'none'
  setupWearable: () => Promise<boolean>
  getWearableHeartRate: () => Promise<WearableData | null>
  checkWearableConnection: () => Promise<boolean>
  enableWearable: () => Promise<boolean>
  disableWearable: () => Promise<void>
}

const WearableContext = createContext<WearableContextType | undefined>(undefined)

export const useWearable = () => {
  const context = useContext(WearableContext)
  if (context === undefined) {
    throw new Error('useWearable must be used within a WearableProvider')
  }
  return context
}

interface WearableProviderProps {
  children: ReactNode
}

export const WearableProvider: React.FC<WearableProviderProps> = ({ children }) => {
  const [hasWearable, setHasWearable] = useState(false)
  const [isWearableConnected, setIsWearableConnected] = useState(false)
  const [isSetup, setIsSetup] = useState(false)
  const [wearableType, setWearableType] = useState<'apple_watch' | 'none'>('none')

  useEffect(() => {
    initializeWearable()
  }, [])

  const initializeWearable = async () => {
    try {
      console.log('⌚ Initializing wearable support...')
      
      // Check if user has configured a wearable
      const wearableEnabled = await AsyncStorage.getItem('wearable_enabled')
      const wearableTypeStored = await AsyncStorage.getItem('wearable_type')
      
      if (wearableEnabled === 'true' && wearableTypeStored) {
        setHasWearable(true)
        setWearableType(wearableTypeStored as 'apple_watch')
        
        // Check if still connected
        const connected = await checkWearableConnection()
        setIsWearableConnected(connected)
      }
      
      setIsSetup(true)
      console.log('✅ Wearable initialization complete')
      
    } catch (error) {
      console.error('❌ Wearable initialization error:', error)
      setIsSetup(true)
    }
  }

  const setupWearable = async (): Promise<boolean> => {
    try {
      console.log('⌚ Setting up Apple Watch integration...')
      
      if (Platform.OS !== 'ios') {
        console.log('⚠️ Apple Watch only supported on iOS')
        return false
      }

      // Check if device can support HealthKit
      if (!Device.isDevice) {
        console.log('⚠️ HealthKit only works on physical devices')
        return false
      }

      // TODO: Implement HealthKit setup when react-native-health is installed
      // const permissions = {
      //   permissions: {
      //     read: [
      //       'HeartRate',
      //       'RestingHeartRate',
      //       'HeartRateVariability'
      //     ],
      //   },
      // }
      // 
      // const authorized = await HealthKit.initHealthKit(permissions)
      // if (!authorized) {
      //   console.log('❌ HealthKit authorization denied')
      //   return false
      // }

      // For now, simulate successful setup
      setHasWearable(true)
      setWearableType('apple_watch')
      setIsWearableConnected(true)
      
      await AsyncStorage.setItem('wearable_enabled', 'true')
      await AsyncStorage.setItem('wearable_type', 'apple_watch')
      
      console.log('✅ Apple Watch setup complete!')
      return true
      
    } catch (error) {
      console.error('❌ Apple Watch setup error:', error)
      return false
    }
  }

  const getWearableHeartRate = async (): Promise<WearableData | null> => {
    try {
      if (!hasWearable || !isWearableConnected) {
        return null
      }

      console.log('💓 Getting heart rate from Apple Watch...')

      // TODO: Implement HealthKit heart rate reading
      // const endDate = new Date()
      // const startDate = new Date()
      // startDate.setMinutes(startDate.getMinutes() - 5)
      // 
      // const heartRateData = await HealthKit.getSamples({
      //   startDate: startDate.toISOString(),
      //   endDate: endDate.toISOString(),
      //   type: 'HeartRate',
      //   limit: 10
      // })
      // 
      // if (heartRateData && heartRateData.length > 0) {
      //   const averageHR = heartRateData.reduce((sum, sample) => sum + sample.value, 0) / heartRateData.length
      //   
      //   return {
      //     heartRate: Math.round(averageHR),
      //     timestamp: new Date().toISOString(),
      //     source: 'apple_watch'
      //   }
      // }

      // For now, simulate heart rate data (remove when HealthKit is implemented)
      const simulatedHR = 72 + Math.random() * 10 // 72-82 BPM
      
      return {
        heartRate: Math.round(simulatedHR),
        timestamp: new Date().toISOString(),
        source: 'apple_watch'
      }
      
    } catch (error) {
      console.error('❌ Get heart rate error:', error)
      return null
    }
  }

  const checkWearableConnection = async (): Promise<boolean> => {
    try {
      if (!hasWearable) {
        return false
      }

      // TODO: Implement HealthKit availability check
      // const available = await HealthKit.isAvailable()
      // return available

      // For now, simulate connection check
      return true
      
    } catch (error) {
      console.error('❌ Check wearable connection error:', error)
      return false
    }
  }

  const enableWearable = async (): Promise<boolean> => {
    try {
      const success = await setupWearable()
      if (success) {
        setHasWearable(true)
        await AsyncStorage.setItem('wearable_enabled', 'true')
      }
      return success
    } catch (error) {
      console.error('❌ Enable wearable error:', error)
      return false
    }
  }

  const disableWearable = async () => {
    try {
      setHasWearable(false)
      setIsWearableConnected(false)
      setWearableType('none')
      
      await AsyncStorage.setItem('wearable_enabled', 'false')
      await AsyncStorage.removeItem('wearable_type')
      
      console.log('⌚ Wearable disabled')
    } catch (error) {
      console.error('❌ Disable wearable error:', error)
    }
  }

  return (
    <WearableContext.Provider
      value={{
        hasWearable,
        isWearableConnected,
        isSetup,
        wearableType,
        setupWearable,
        getWearableHeartRate,
        checkWearableConnection,
        enableWearable,
        disableWearable,
      }}
    >
      {children}
    </WearableContext.Provider>
  )
}