// File: mobile/contexts/AuthContext.tsx
// Fixed to handle existing user profiles and prevent duplicates
import React, { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import * as Linking from 'expo-linking'
import { supabase } from '../lib/supabase'
import { signInWithGoogle, signInWithApple, handleAuthCallback } from '../lib/socialAuth'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signInWithGoogle: () => Promise<any>
  signInWithApple: () => Promise<any>
  signOut: () => Promise<void>
  clearAuthCache: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  // Enhanced profile creation with duplicate checking
  const createUserProfileSafe = async (user: User) => {
    try {
      console.log('🔍 Checking if profile exists for:', user.email)
      
      // First check if profile already exists
      const { data: existingProfile, error: checkError } = await supabase
        .from('user_profiles')
        .select('id')
        .eq('id', user.id)
        .single()

      if (existingProfile) {
        console.log('✅ Profile already exists, no need to create')
        return { success: true, existed: true }
      }

      if (checkError && checkError.code !== 'PGRST116') { // PGRST116 = no rows found (expected)
        console.log('⚠️ Error checking existing profile:', checkError)
      }

      // Profile doesn't exist, create it
      console.log('➕ Creating new user profile...')
      const { data: newProfile, error: createError } = await supabase
        .from('user_profiles')
        .insert({
          id: user.id,
          email: user.email || '',
          first_name: user.user_metadata?.first_name || '',
          last_name: user.user_metadata?.last_name || '',
          avatar_url: user.user_metadata?.avatar_url || null,
        })
        .select()
        .single()

      if (createError) {
        // Handle duplicate key error gracefully
        if (createError.code === '23505') {
          console.log('✅ Profile already exists (created by trigger), continuing...')
          return { success: true, existed: true }
        }
        console.error('❌ Error creating profile:', createError)
        return { success: false, error: createError }
      }

      console.log('✅ Profile created successfully:', newProfile)
      return { success: true, existed: false, profile: newProfile }

    } catch (error) {
      console.error('❌ Exception creating profile:', error)
      return { success: false, error }
    }
  }

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Error getting initial session:', error)
        } else {
          console.log('Auth state changed:', session ? 'SIGNED_IN' : 'INITIAL_SESSION')
          setSession(session)
          setUser(session?.user ?? null)
          
          // Create profile if user exists but we haven't created one yet
          if (session?.user) {
            await createUserProfileSafe(session.user)
          }
        }
      } catch (error) {
        console.error('Exception getting initial session:', error)
      } finally {
        setLoading(false)
      }
    }

    getInitialSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event, session ? 'SIGNED_IN' : 'SIGNED_OUT')
        setSession(session)
        setUser(session?.user ?? null)
        
        // Create profile for new users
        if (event === 'SIGNED_IN' && session?.user) {
          await createUserProfileSafe(session.user)
        }
        
        setLoading(false)
      }
    )

    // Handle deep links for OAuth callbacks
    const handleUrl = (url: string) => {
      console.log('🔗 Handling deep link:', url)
      handleAuthCallback(url)
    }

    // Listen for incoming links
    const subscription2 = Linking.addEventListener('url', ({ url }) => handleUrl(url))

    return () => {
      subscription?.unsubscribe()
      subscription2?.remove()
    }
  }, [])

  // Google Sign-In
  const signInWithGoogleOAuth = async () => {
    try {
      setLoading(true)
      console.log('🔵 Starting Google OAuth sign-in...')
      const result = await signInWithGoogle()
      
      if (result.success) {
        console.log('✅ Google sign-in successful')
      } else {
        console.log('❌ Google sign-in failed:', result.error)
      }
      
      return result
    } catch (error) {
      console.error('❌ Google sign-in exception:', error)
      return { success: false, error }
    } finally {
      setLoading(false)
    }
  }

  // Apple Sign-In
  const signInWithAppleOAuth = async () => {
    try {
      setLoading(true)
      console.log('🍎 Starting Apple OAuth sign-in...')
      const result = await signInWithApple()
      
      if (result.success) {
        console.log('✅ Apple sign-in successful')
      } else {
        console.log('❌ Apple sign-in failed:', result.error)
      }
      
      return result
    } catch (error) {
      console.error('❌ Apple sign-in exception:', error)
      return { success: false, error }
    } finally {
      setLoading(false)
    }
  }

  // Sign out
  const signOut = async () => {
    try {
      console.log('👋 Signing out...')
      await clearAuthCache()
      const { error } = await supabase.auth.signOut()
      
      if (error) {
        console.error('Sign out error:', error)
      } else {
        console.log('✅ Signed out successfully')
      }
    } catch (error) {
      console.error('Exception during sign out:', error)
    }
  }

  // Clear authentication cache
  const clearAuthCache = async () => {
    try {
      console.log('🧹 Clearing auth cache...')
      
      // Clear any cached user data
      setUser(null)
      setSession(null)
      
      console.log('✅ Auth cache cleared')
    } catch (error) {
      console.error('Error clearing auth cache:', error)
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

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}