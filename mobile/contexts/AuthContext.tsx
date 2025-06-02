// Updated AuthContext - mobile/contexts/AuthContext.tsx
// Integrated with Google and Apple social login

import React, { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import * as Linking from 'expo-linking'
import { supabase, createUserProfile } from '../lib/supabase'
import { signInWithGoogle, signInWithApple, handleAuthCallback } from '../lib/socialAuth'
import * as SecureStore from 'expo-secure-store'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signInWithGoogle: () => Promise<any>
  signInWithApple: () => Promise<any>
  signOut: () => Promise<void>
  clearAuthCache: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  // Clear all auth cache
  const clearAuthCache = async () => {
    try {
      console.log('🧹 Clearing auth cache...')
      
      // Clear SecureStore auth data
      await SecureStore.deleteItemAsync('supabase-auth-token')
      await SecureStore.deleteItemAsync('sb-lteeihdzrgxlgedmwwfk-auth-token')
      
      // Clear any other possible auth keys
      const possibleKeys = [
        'supabase.auth.token',
        'sb-auth-token',
        'auth-token',
        'access_token',
        'refresh_token'
      ]
      
      for (const key of possibleKeys) {
        try {
          await SecureStore.deleteItemAsync(key)
        } catch (e) {
          // Key might not exist, that's fine
        }
      }
      
      console.log('✅ Auth cache cleared')
    } catch (error) {
      console.error('❌ Error clearing auth cache:', error)
    }
  }

  useEffect(() => {
    // Handle deep links for OAuth callbacks
    const subscription = Linking.addEventListener('url', async ({ url }) => {
      console.log('🔗 Deep link received:', url)
      
      if (url.includes('auth/callback')) {
        const result = await handleAuthCallback(url)
        if (result.success) {
          console.log('✅ OAuth callback handled successfully')
        } else {
          console.error('❌ OAuth callback failed:', result.error)
        }
      }
    })

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const { data: { subscription: authSubscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event)
        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)

        // Handle different auth events
        if (event === 'SIGNED_IN' && session?.user) {
          console.log('🔄 User signed in, checking/creating profile...')
          
          // For social login, create profile if it doesn't exist
          const result = await createUserProfile(session.user)
          if (result.success) {
            console.log('✅ Profile created/verified successfully')
          } else {
            // Profile might already exist, that's fine for social login
            console.log('ℹ️ Profile creation skipped (might already exist)')
          }
        }
        
        if (event === 'SIGNED_OUT') {
          console.log('🔄 User signed out, clearing cache...')
          await clearAuthCache()
        }
      }
    )

    return () => {
      subscription?.remove()
      authSubscription.unsubscribe()
    }
  }, [])

  const signInWithGoogleOAuth = async () => {
    try {
      setLoading(true)
      console.log('🔄 Starting Google OAuth sign-in...')
      
      const result = await signInWithGoogle()
      
      if (result.success) {
        console.log('✅ Google sign-in successful')
        return { success: true, data: result.data }
      } else {
        console.error('❌ Google sign-in failed:', result.error)
        return { success: false, error: result.error }
      }
    } catch (error) {
      console.error('💥 Google sign-in exception:', error)
      return { success: false, error }
    } finally {
      setLoading(false)
    }
  }

  const signInWithAppleOAuth = async () => {
    try {
      setLoading(true)
      console.log('🔄 Starting Apple OAuth sign-in...')
      
      const result = await signInWithApple()
      
      if (result.success) {
        console.log('✅ Apple sign-in successful')
        return { success: true, data: result.data }
      } else {
        console.error('❌ Apple sign-in failed:', result.error)
        return { success: false, error: result.error }
      }
    } catch (error) {
      console.error('💥 Apple sign-in exception:', error)
      return { success: false, error }
    } finally {
      setLoading(false)
    }
  }

  const signOut = async () => {
    try {
      setLoading(true)
      console.log('🔄 Signing out...')
      
      const { error } = await supabase.auth.signOut()
      if (error) {
        console.error('❌ Sign out error:', error)
      } else {
        console.log('✅ Signed out successfully')
      }
      
      // Clear cache after sign out
      await clearAuthCache()
    } catch (err) {
      console.error('💥 Sign out exception:', err)
    } finally {
      setLoading(false)
    }
  }

  const value = {
    user,
    session,
    loading,
    signInWithGoogle: signInWithGoogleOAuth,
    signInWithApple: signInWithAppleOAuth,
    signOut,
    clearAuthCache,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}