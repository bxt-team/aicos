import React, { createContext, useContext, useEffect, useState } from 'react'
import { Session, User, AuthError } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  error: AuthError | null
  
  // Email/Password methods
  signUp: (email: string, password: string, metadata?: any) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  
  // Password reset
  resetPassword: (email: string) => Promise<void>
  updatePassword: (newPassword: string) => Promise<void>
  
  // Magic link
  signInWithMagicLink: (email: string) => Promise<void>
  
  // OAuth
  signInWithGoogle: () => Promise<void>
  signInWithGitHub: () => Promise<void>
  signInWithApple: () => Promise<void>
  
  // MFA
  enrollMFA: () => Promise<{ qr: string; secret: string; factorId: string }>
  verifyMFA: (factorId: string, code: string) => Promise<void>
  unenrollMFA: (factorId: string) => Promise<void>
  listMFAFactors: () => Promise<any[]>
  getAAL: () => Promise<{ currentLevel: string; nextLevel: string }>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useSupabaseAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useSupabaseAuth must be used within SupabaseAuthProvider')
  }
  return context
}

export const SupabaseAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<AuthError | null>(null)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes with debounce to prevent rapid updates
    let timeoutId: NodeJS.Timeout;
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      // Ignore token refreshed events to prevent unnecessary re-renders
      if (event === 'TOKEN_REFRESHED') {
        return;
      }
      
      // Clear any pending updates
      clearTimeout(timeoutId);
      
      // Debounce the state update
      timeoutId = setTimeout(() => {
        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)
      }, 100);
    })

    return () => {
      clearTimeout(timeoutId);
      subscription.unsubscribe();
    }
  }, [])

  // Email/Password methods
  const signUp = async (email: string, password: string, metadata?: any) => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: metadata,
        },
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const signIn = async (email: string, password: string) => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const signOut = async () => {
    try {
      setError(null)
      const { error } = await supabase.auth.signOut()
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  // Password reset
  const resetPassword = async (email: string) => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const updatePassword = async (newPassword: string) => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.updateUser({
        password: newPassword,
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  // Magic link
  const signInWithMagicLink = async (email: string) => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  // OAuth providers
  const signInWithGoogle = async () => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const signInWithGitHub = async () => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const signInWithApple = async () => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'apple',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  // MFA methods
  const enrollMFA = async () => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.mfa.enroll({
        factorType: 'totp',
      })
      if (error) throw error
      return {
        qr: data.totp.qr_code,
        secret: data.totp.secret,
        factorId: data.id,
      }
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const verifyMFA = async (factorId: string, code: string) => {
    try {
      setError(null)
      // Create challenge
      const { data: challengeData, error: challengeError } = await supabase.auth.mfa.challenge({
        factorId,
      })
      if (challengeError) throw challengeError

      // Verify challenge
      const { data, error } = await supabase.auth.mfa.verify({
        factorId,
        challengeId: challengeData.id,
        code,
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const unenrollMFA = async (factorId: string) => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.mfa.unenroll({
        factorId,
      })
      if (error) throw error
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const listMFAFactors = async () => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.mfa.listFactors()
      if (error) throw error
      return [...(data.totp || []), ...(data.phone || [])]
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const getAAL = async () => {
    try {
      setError(null)
      const { data, error } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel()
      if (error) throw error
      return {
        currentLevel: data.currentLevel || 'aal1',
        nextLevel: data.nextLevel || 'aal1',
      }
    } catch (err) {
      setError(err as AuthError)
      throw err
    }
  }

  const value: AuthContextType = {
    user,
    session,
    loading,
    error,
    signUp,
    signIn,
    signOut,
    resetPassword,
    updatePassword,
    signInWithMagicLink,
    signInWithGoogle,
    signInWithGitHub,
    signInWithApple,
    enrollMFA,
    verifyMFA,
    unenrollMFA,
    listMFAFactors,
    getAAL,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}