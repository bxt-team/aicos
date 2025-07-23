import React, { useState, useEffect } from 'react'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import { RateLimitError } from './RateLimitError'
import '../../styles/auth-branded.css'

export const BrandedSupabaseLogin: React.FC = () => {
  const navigate = useNavigate()
  const { signIn, signInWithMagicLink, signInWithGoogle, signInWithGitHub, signInWithApple, error } = useSupabaseAuth()
  
  const [activeTab, setActiveTab] = useState<'password' | 'magic'>('password')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    // Apply auth page class to body
    document.body.classList.add('auth-page')
    return () => {
      document.body.classList.remove('auth-page')
    }
  }, [])

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError('')
    setLoading(true)
    
    try {
      await signIn(email, password)
      navigate('/dashboard')
    } catch (err: any) {
      setLocalError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleMagicLinkLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError('')
    setLoading(true)
    
    try {
      await signInWithMagicLink(email)
      setSuccessMessage('Magic link sent! Check your email.')
      setEmail('')
    } catch (err: any) {
      setLocalError(err.message || 'Failed to send magic link')
    } finally {
      setLoading(false)
    }
  }

  const handleOAuthSignIn = async (provider: 'google' | 'github' | 'apple') => {
    setLoading(true)
    setLocalError('')
    try {
      switch (provider) {
        case 'google':
          await signInWithGoogle()
          break
        case 'github':
          await signInWithGitHub()
          break
        case 'apple':
          await signInWithApple()
          break
      }
    } catch (err: any) {
      setLocalError(err.message || `${provider} sign in failed`)
    } finally {
      setLoading(false)
    }
  }

  const displayError = localError || error?.message

  return (
    <div className="auth-page-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo-container">
            <img src="/logo.svg" alt="AICOS Logo" className="auth-logo" />
            <h1 className="auth-brand-name">AICOS</h1>
            <p className="auth-brand-tagline">Where AI runs your business.</p>
          </div>
        </div>
        
        <div className="auth-content">
          <h2 className="auth-title">Welcome back</h2>
          <p className="auth-subtitle">Sign in to continue to your workspace</p>
          
          <RateLimitError error={displayError} />
          
          {successMessage && (
            <div className="auth-success">
              {successMessage}
            </div>
          )}
          
          <div className="auth-tabs">
            <button
              className={`auth-tab ${activeTab === 'password' ? 'active' : ''}`}
              onClick={() => setActiveTab('password')}
            >
              Password
            </button>
            <button
              className={`auth-tab ${activeTab === 'magic' ? 'active' : ''}`}
              onClick={() => setActiveTab('magic')}
            >
              Magic Link
            </button>
          </div>
          
          {activeTab === 'password' ? (
            <form onSubmit={handlePasswordLogin} className="auth-form">
              <div className="auth-form-group">
                <label htmlFor="email" className="auth-label">Email</label>
                <input
                  id="email"
                  type="email"
                  className="auth-input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>
              
              <div className="auth-form-group">
                <label htmlFor="password" className="auth-label">Password</label>
                <input
                  id="password"
                  type="password"
                  className="auth-input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>
              
              <button type="submit" className="auth-button" disabled={loading}>
                {loading ? <span className="auth-spinner" /> : 'Sign In'}
              </button>
              
              <div className="auth-links">
                <RouterLink to="/forgot-password" className="auth-link">
                  Forgot password?
                </RouterLink>
                <RouterLink to="/signup" className="auth-link">
                  Create account
                </RouterLink>
              </div>
            </form>
          ) : (
            <form onSubmit={handleMagicLinkLogin} className="auth-form">
              <div className="auth-form-group">
                <label htmlFor="magic-email" className="auth-label">Email</label>
                <input
                  id="magic-email"
                  type="email"
                  className="auth-input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>
              
              <button type="submit" className="auth-button" disabled={loading}>
                {loading ? <span className="auth-spinner" /> : 'Send Magic Link'}
              </button>
              
              <div className="auth-links center">
                <RouterLink to="/signup" className="auth-link">
                  Don't have an account? Sign up
                </RouterLink>
              </div>
            </form>
          )}
          
          <div className="auth-divider">
            <span>Or continue with</span>
          </div>
          
          <div className="oauth-buttons">
            <button
              className="oauth-button"
              onClick={() => handleOAuthSignIn('google')}
              disabled={loading}
            >
              <svg viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </button>
            
            <button
              className="oauth-button"
              onClick={() => handleOAuthSignIn('github')}
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              Continue with GitHub
            </button>
            
            <button
              className="oauth-button"
              onClick={() => handleOAuthSignIn('apple')}
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
              </svg>
              Continue with Apple
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}