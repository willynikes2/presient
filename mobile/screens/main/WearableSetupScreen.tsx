// screens/main/WearableSetupScreen.tsx - Apple Watch Setup Flow
import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native'
import { useNavigation } from '@react-navigation/native'
import { useWearable } from '../../contexts/WearableContext'

export default function WearableSetupScreen() {
  const navigation = useNavigation()
  const { setupWearable, getWearableHeartRate, hasWearable } = useWearable()
  
  const [currentStep, setCurrentStep] = useState<'question' | 'setup' | 'recording' | 'complete'>('question')
  const [isLoading, setIsLoading] = useState(false)
  const [heartRateData, setHeartRateData] = useState<any>(null)

  useEffect(() => {
    if (hasWearable) {
      setCurrentStep('complete')
    }
  }, [hasWearable])

  const handleHasWearable = async (hasDevice: boolean) => {
    if (!hasDevice) {
      // Skip to biometric enrollment
      navigation.navigate('BiometricEnrollment' as never)
      return
    }

    setCurrentStep('setup')
  }

  const handleSetupWearable = async () => {
    try {
      setIsLoading(true)
      console.log('⌚ Starting Apple Watch setup...')
      
      const success = await setupWearable()
      
      if (success) {
        setCurrentStep('recording')
        // Wait a moment then get heart rate
        setTimeout(async () => {
          await recordWearableHeartRate()
        }, 2000)
      } else {
        Alert.alert(
          'Setup Failed',
          'Unable to connect to Apple Watch. Please check that HealthKit permissions are enabled.',
          [
            { text: 'Try Again', onPress: () => setCurrentStep('setup') },
            { text: 'Skip', onPress: () => navigation.navigate('BiometricEnrollment' as never) }
          ]
        )
      }
    } catch (error) {
      console.error('❌ Wearable setup error:', error)
      Alert.alert('Error', 'An error occurred during setup')
    } finally {
      setIsLoading(false)
    }
  }

  const recordWearableHeartRate = async () => {
    try {
      console.log('💓 Recording heart rate from Apple Watch...')
      
      const data = await getWearableHeartRate()
      
      if (data) {
        setHeartRateData(data)
        setCurrentStep('complete')
        console.log('✅ Wearable heart rate recorded:', data)
      } else {
        Alert.alert(
          'Recording Failed',
          'Unable to get heart rate from Apple Watch. Please ensure it\'s connected and try again.',
          [
            { text: 'Retry', onPress: recordWearableHeartRate },
            { text: 'Skip', onPress: () => navigation.navigate('BiometricEnrollment' as never) }
          ]
        )
      }
    } catch (error) {
      console.error('❌ Heart rate recording error:', error)
      Alert.alert('Error', 'Failed to record heart rate data')
    }
  }

  const proceedToEnrollment = () => {
    navigation.navigate('BiometricEnrollment' as never)
  }

  const renderQuestionStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.emoji}>⌚</Text>
      <Text style={styles.title}>Do you have a wearable?</Text>
      <Text style={styles.subtitle}>
        Apple Watch or other heart rate wearables improve authentication accuracy and provide fallback support.
      </Text>
      
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={() => handleHasWearable(true)}
        >
          <Text style={styles.buttonText}>✅ Yes, I have Apple Watch</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={() => handleHasWearable(false)}
        >
          <Text style={[styles.buttonText, styles.secondaryButtonText]}>❌ No, skip this step</Text>
        </TouchableOpacity>
      </View>
      
      <View style={styles.benefitsContainer}>
        <Text style={styles.benefitsTitle}>Benefits of Apple Watch:</Text>
        <Text style={styles.benefit}>• Higher authentication accuracy</Text>
        <Text style={styles.benefit}>• Fallback if phone sensor fails</Text>
        <Text style={styles.benefit}>• Real-time heart rate monitoring</Text>
        <Text style={styles.benefit}>• Medical-grade accuracy</Text>
      </View>
    </View>
  )

  const renderSetupStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.emoji}>🔧</Text>
      <Text style={styles.title}>Apple Watch Setup</Text>
      <Text style={styles.subtitle}>
        We'll connect to your Apple Watch to access heart rate data for biometric authentication.
      </Text>
      
      <View style={styles.instructionsContainer}>
        <Text style={styles.instructionTitle}>Setup Instructions:</Text>
        <Text style={styles.instruction}>1. Ensure Apple Watch is paired and connected</Text>
        <Text style={styles.instruction}>2. Grant HealthKit permissions when prompted</Text>
        <Text style={styles.instruction}>3. Allow heart rate data access</Text>
        <Text style={styles.instruction}>4. Keep your watch on during setup</Text>
      </View>
      
      <TouchableOpacity
        style={[styles.button, styles.primaryButton]}
        onPress={handleSetupWearable}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#ffffff" />
        ) : (
          <Text style={styles.buttonText}>🚀 Setup Apple Watch</Text>
        )}
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.button, styles.secondaryButton]}
        onPress={() => navigation.navigate('BiometricEnrollment' as never)}
      >
        <Text style={[styles.buttonText, styles.secondaryButtonText]}>Skip for now</Text>
      </TouchableOpacity>
    </View>
  )

  const renderRecordingStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.emoji}>💓</Text>
      <Text style={styles.title}>Recording Heart Rate</Text>
      <Text style={styles.subtitle}>
        Getting baseline heart rate data from your Apple Watch...
      </Text>
      
      <View style={styles.recordingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.recordingText}>Please keep your Apple Watch on</Text>
        <Text style={styles.recordingSubtext}>This may take a few moments</Text>
      </View>
    </View>
  )

  const renderCompleteStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.emoji}>✅</Text>
      <Text style={styles.title}>Apple Watch Connected!</Text>
      <Text style={styles.subtitle}>
        Your wearable is now set up for enhanced biometric authentication.
      </Text>
      
      {heartRateData && (
        <View style={styles.dataContainer}>
          <Text style={styles.dataTitle}>Heart Rate Data:</Text>
          <Text style={styles.dataValue}>{heartRateData.heartRate} BPM</Text>
          <Text style={styles.dataSource}>Source: Apple Watch</Text>
        </View>
      )}
      
      <View style={styles.featuresContainer}>
        <Text style={styles.featureTitle}>What's Next:</Text>
        <Text style={styles.feature}>• Dual-sensor authentication (Phone + Watch)</Text>
        <Text style={styles.feature}>• Higher confidence scores</Text>
        <Text style={styles.feature}>• Automatic fallback support</Text>
        <Text style={styles.feature}>• Continuous heart rate monitoring</Text>
      </View>
      
      <TouchableOpacity
        style={[styles.button, styles.primaryButton]}
        onPress={proceedToEnrollment}
      >
        <Text style={styles.buttonText}>Continue to Biometric Enrollment</Text>
      </TouchableOpacity>
    </View>
  )

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {currentStep === 'question' && renderQuestionStep()}
      {currentStep === 'setup' && renderSetupStep()}
      {currentStep === 'recording' && renderRecordingStep()}
      {currentStep === 'complete' && renderCompleteStep()}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  contentContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  stepContainer: {
    alignItems: 'center',
  },
  emoji: {
    fontSize: 64,
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#94a3b8',
    textAlign: 'center',
    marginBottom: 30,
    paddingHorizontal: 20,
    lineHeight: 22,
  },
  buttonContainer: {
    width: '100%',
    marginBottom: 30,
  },
  button: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginBottom: 12,
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#3b82f6',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#475569',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  secondaryButtonText: {
    color: '#94a3b8',
  },
  benefitsContainer: {
    backgroundColor: '#1e293b',
    padding: 20,
    borderRadius: 12,
    width: '100%',
  },
  benefitsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e2e8f0',
    marginBottom: 12,
  },
  benefit: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 6,
  },
  instructionsContainer: {
    backgroundColor: '#1e293b',
    padding: 20,
    borderRadius: 12,
    width: '100%',
    marginBottom: 20,
  },
  instructionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e2e8f0',
    marginBottom: 12,
  },
  instruction: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 8,
  },
  recordingContainer: {
    alignItems: 'center',
    marginVertical: 40,
  },
  recordingText: {
    fontSize: 16,
    color: '#e2e8f0',
    marginTop: 20,
  },
  recordingSubtext: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 8,
  },
  dataContainer: {
    backgroundColor: '#1e293b',
    padding: 20,
    borderRadius: 12,
    width: '100%',
    marginBottom: 20,
    alignItems: 'center',
  },
  dataTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e2e8f0',
    marginBottom: 8,
  },
  dataValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#3b82f6',
    marginBottom: 4,
  },
  dataSource: {
    fontSize: 14,
    color: '#94a3b8',
  },
  featuresContainer: {
    backgroundColor: '#1e293b',
    padding: 20,
    borderRadius: 12,
    width: '100%',
    marginBottom: 20,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e2e8f0',
    marginBottom: 12,
  },
  feature: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 6,
  },
})