// Social Login Screen - mobile/screens/auth/SocialLoginScreen.tsx
// Clean Google and Apple Sign-In interface

import React, { useState } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  Image,
} from 'react-native'
import { useAuth } from '../../contexts/AuthContext'

const SocialLoginScreen = () => {
  const { signInWithGoogle, signInWithApple, loading } = useAuth()
  const [googleLoading, setGoogleLoading] = useState(false)
  const [appleLoading, setAppleLoading] = useState(false)

  const handleGoogleSignIn = async () => {
    try {
      setGoogleLoading(true)
      const result = await signInWithGoogle()
      
      if (!result.success) {
        Alert.alert(
          'Sign In Failed',
          result.error?.message || 'Something went wrong with Google sign-in'
        )
      }
      // Success is handled by auth state change
    } catch (error) {
      Alert.alert('Error', 'Google sign-in failed. Please try again.')
    } finally {
      setGoogleLoading(false)
    }
  }

  const handleAppleSignIn = async () => {
    try {
      setAppleLoading(true)
      const result = await signInWithApple()
      
      if (!result.success) {
        Alert.alert(
          'Sign In Failed', 
          result.error?.message || 'Something went wrong with Apple sign-in'
        )
      }
      // Success is handled by auth state change
    } catch (error) {
      Alert.alert('Error', 'Apple sign-in failed. Please try again.')
    } finally {
      setAppleLoading(false)
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo/Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Presient</Text>
          <Text style={styles.subtitle}>Smart Presence Switch</Text>
          <Text style={styles.description}>
            Sign in to enroll your family members and manage biometric authentication
          </Text>
        </View>

        {/* Social Login Buttons */}
        <View style={styles.buttonContainer}>
          {/* Google Sign-In Button */}
          <TouchableOpacity
            style={styles.googleButton}
            onPress={handleGoogleSignIn}
            disabled={loading || googleLoading}
          >
            <View style={styles.buttonContent}>
              {googleLoading ? (
                <ActivityIndicator color="#000000" size="small" />
              ) : (
                <>
                  <View style={styles.googleIcon}>
                    <Text style={styles.googleIconText}>G</Text>
                  </View>
                  <Text style={styles.googleButtonText}>Continue with Google</Text>
                </>
              )}
            </View>
          </TouchableOpacity>

          {/* Apple Sign-In Button */}
          <TouchableOpacity
            style={styles.appleButton}
            onPress={handleAppleSignIn}
            disabled={loading || appleLoading}
          >
            <View style={styles.buttonContent}>
              {appleLoading ? (
                <ActivityIndicator color="#ffffff" size="small" />
              ) : (
                <>
                  <View style={styles.appleIcon}>
                    <Text style={styles.appleIconText}>🍎</Text>
                  </View>
                  <Text style={styles.appleButtonText}>Continue with Apple</Text>
                </>
              )}
            </View>
          </TouchableOpacity>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            By signing in, you agree to our Terms of Service and Privacy Policy
          </Text>
        </View>
      </View>
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
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#64748b',
    marginBottom: 24,
  },
  description: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 24,
  },
  buttonContainer: {
    width: '100%',
    maxWidth: 300,
    gap: 16,
  },
  googleButton: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  appleButton: {
    backgroundColor: '#000000',
    borderRadius: 12,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  googleIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#ea4335',
    justifyContent: 'center',
    alignItems: 'center',
  },
  googleIconText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  googleButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '600',
  },
  appleIcon: {
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  appleIconText: {
    fontSize: 18,
  },
  appleButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  footer: {
    marginTop: 48,
    paddingHorizontal: 16,
  },
  footerText: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 18,
  },
})

export default SocialLoginScreen