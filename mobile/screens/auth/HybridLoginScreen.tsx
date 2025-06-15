// File: mobile/screens/auth/HybridLoginScreen.tsx
// Copy this entire content into the file

import React, { useState } from 'react'
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  TextInput,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native'
import { useAuth } from '../../contexts/AuthContext'
import { supabase } from '../../lib/supabase'

const HybridLoginScreen = () => {
  const { signInWithGoogle, signInWithApple, loading } = useAuth()
  const [googleLoading, setGoogleLoading] = useState(false)
  const [appleLoading, setAppleLoading] = useState(false)
  const [emailLoading, setEmailLoading] = useState(false)
  
  // Email/Password form state
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')

  // Social login handlers
  const handleGoogleSignIn = async () => {
    try {
      setGoogleLoading(true)
      Alert.alert('Google OAuth', 'Google OAuth not configured yet. Use email/password below for now.')
    } catch (error) {
      Alert.alert('Error', 'Google sign-in failed. Please try again.')
    } finally {
      setGoogleLoading(false)
    }
  }

  const handleAppleSignIn = async () => {
    try {
      setAppleLoading(true)
      Alert.alert('Apple OAuth', 'Apple OAuth not configured yet. Use email/password below for now.')
    } catch (error) {
      Alert.alert('Error', 'Apple sign-in failed. Please try again.')
    } finally {
      setAppleLoading(false)
    }
  }

  // Email/Password handlers
  const handleEmailSignIn = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter both email and password')
      return
    }

    try {
      setEmailLoading(true)
      console.log('🔄 Attempting email sign in...')
      
      const { error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password: password,
      })

      if (error) {
        console.error('❌ Email sign in error:', error)
        Alert.alert('Sign In Failed', error.message)
      } else {
        console.log('✅ Email sign in successful')
      }
    } catch (error) {
      console.error('💥 Email sign in exception:', error)
      Alert.alert('Error', 'Sign in failed. Please try again.')
    } finally {
      setEmailLoading(false)
    }
  }

  const handleEmailSignUp = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter both email and password')
      return
    }

    if (password.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters')
      return
    }

    try {
      setEmailLoading(true)
      console.log('🔄 Attempting email sign up...')
      
      const { error } = await supabase.auth.signUp({
        email: email.trim(),
        password: password,
        options: {
          data: {
            first_name: firstName.trim(),
            last_name: lastName.trim(),
          }
        }
      })

      if (error) {
        console.error('❌ Email sign up error:', error)
        Alert.alert('Sign Up Failed', error.message)
      } else {
        console.log('✅ Email sign up successful')
        Alert.alert(
          'Sign Up Successful', 
          'Please check your email for confirmation link, then try signing in.'
        )
        setIsSignUp(false) // Switch to sign in mode
      }
    } catch (error) {
      console.error('💥 Email sign up exception:', error)
      Alert.alert('Error', 'Sign up failed. Please try again.')
    } finally {
      setEmailLoading(false)
    }
  }

  const toggleAuthMode = () => {
    setIsSignUp(!isSignUp)
    setEmail('')
    setPassword('')
    setFirstName('')
    setLastName('')
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Presient</Text>
            <Text style={styles.subtitle}>Smart Presence Switch</Text>
          </View>

          {/* Social Login Section */}
          <View style={styles.socialSection}>
            <Text style={styles.sectionTitle}>Quick Sign In</Text>
            
            <View style={styles.socialButtons}>
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
          </View>

          {/* Divider */}
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>or</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Email/Password Section */}
          <View style={styles.emailSection}>
            <Text style={styles.sectionTitle}>
              {isSignUp ? 'Create Account' : 'Sign In with Email'}
            </Text>

            {/* Name fields for sign up */}
            {isSignUp && (
              <View style={styles.nameRow}>
                <View style={styles.nameInput}>
                  <Text style={styles.inputLabel}>First Name</Text>
                  <TextInput
                    style={styles.textInput}
                    value={firstName}
                    onChangeText={setFirstName}
                    placeholder="John"
                    placeholderTextColor="#64748b"
                    autoCapitalize="words"
                  />
                </View>
                <View style={styles.nameInput}>
                  <Text style={styles.inputLabel}>Last Name</Text>
                  <TextInput
                    style={styles.textInput}
                    value={lastName}
                    onChangeText={setLastName}
                    placeholder="Smith"
                    placeholderTextColor="#64748b"
                    autoCapitalize="words"
                  />
                </View>
              </View>
            )}

            {/* Email */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Email</Text>
              <TextInput
                style={styles.textInput}
                value={email}
                onChangeText={setEmail}
                placeholder="your@email.com"
                placeholderTextColor="#64748b"
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Password */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Password</Text>
              <TextInput
                style={styles.textInput}
                value={password}
                onChangeText={setPassword}
                placeholder={isSignUp ? "At least 6 characters" : "Your password"}
                placeholderTextColor="#64748b"
                secureTextEntry
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Submit Button */}
            <TouchableOpacity
              style={styles.emailButton}
              onPress={isSignUp ? handleEmailSignUp : handleEmailSignIn}
              disabled={loading || emailLoading}
            >
              {emailLoading ? (
                <ActivityIndicator color="#ffffff" size="small" />
              ) : (
                <Text style={styles.emailButtonText}>
                  {isSignUp ? 'Create Account' : 'Sign In'}
                </Text>
              )}
            </TouchableOpacity>

            {/* Toggle Auth Mode */}
            <TouchableOpacity onPress={toggleAuthMode} style={styles.toggleButton}>
              <Text style={styles.toggleText}>
                {isSignUp 
                  ? 'Already have an account? Sign In' 
                  : "Don't have an account? Sign Up"
                }
              </Text>
            </TouchableOpacity>
          </View>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              By signing in, you agree to our Terms of Service and Privacy Policy
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingVertical: 32,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
  },
  socialSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 16,
  },
  socialButtons: {
    gap: 12,
  },
  googleButton: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    height: 52,
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
    height: 52,
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
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#ea4335',
    justifyContent: 'center',
    alignItems: 'center',
  },
  googleIconText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  googleButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '600',
  },
  appleIcon: {
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  appleIconText: {
    fontSize: 16,
  },
  appleButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#334155',
  },
  dividerText: {
    color: '#64748b',
    fontSize: 14,
    marginHorizontal: 16,
  },
  emailSection: {
    marginBottom: 24,
  },
  nameRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  nameInput: {
    flex: 1,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#1e293b',
    borderRadius: 8,
    padding: 16,
    color: '#ffffff',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  emailButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 12,
    height: 52,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  emailButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  toggleButton: {
    marginTop: 16,
    alignItems: 'center',
  },
  toggleText: {
    color: '#3b82f6',
    fontSize: 14,
    fontWeight: '500',
  },
  footer: {
    marginTop: 32,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 18,
  },
})

export default HybridLoginScreen