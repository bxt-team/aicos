import React, { useState, useEffect } from 'react'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { Link as RouterLink } from 'react-router-dom'
import '../../styles/auth-branded.css'

export const BrandedForgotPassword: React.FC = () => {
  const { resetPassword, error } = useSupabaseAuth()
  const [email, setEmail] = useState('')
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError('')
    setLoading(true)
    
    try {
      await resetPassword(email)
      setSuccessMessage('Password reset link sent! Check your email.')
      setEmail('')
    } catch (err: any) {
      setLocalError(err.message || 'Failed to send reset link')
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
          <h2 className="auth-title">Reset your password</h2>
          <p className="auth-subtitle">
            Enter your email address and we'll send you a link to reset your password
          </p>
          
          {displayError && (
            <div className="auth-error">
              {displayError}
            </div>
          )}
          
          {successMessage && (
            <div className="auth-success">
              {successMessage}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="auth-form">
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
                autoFocus
              />
            </div>
            
            <button type="submit" className="auth-button" disabled={loading}>
              {loading ? <span className="auth-spinner" /> : 'Send Reset Link'}
            </button>
            
            <div className="auth-links center" style={{ marginTop: '24px' }}>
              <RouterLink to="/login" className="auth-link">
                ← Back to sign in
              </RouterLink>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}