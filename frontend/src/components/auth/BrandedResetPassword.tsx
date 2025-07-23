import React, { useState, useEffect } from 'react'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { useNavigate, useLocation } from 'react-router-dom'
import { supabase } from '../../lib/supabase'
import { RateLimitError } from './RateLimitError'
import '../../styles/auth-branded.css'

export const BrandedResetPassword: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { updatePassword, error } = useSupabaseAuth()
  
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [localError, setLocalError] = useState('')
  const [isValidToken, setIsValidToken] = useState(false)
  const [checkingToken, setCheckingToken] = useState(true)

  useEffect(() => {
    // Apply auth page class to body
    document.body.classList.add('auth-page')
    
    // Check if we have a valid reset token in the URL
    checkResetToken()
    
    return () => {
      document.body.classList.remove('auth-page')
    }
  }, [location])

  const checkResetToken = async () => {
    try {
      setCheckingToken(true)
      const hashParams = new URLSearchParams(location.hash.substring(1))
      const accessToken = hashParams.get('access_token')
      const refreshToken = hashParams.get('refresh_token')
      const type = hashParams.get('type')
      const errorCode = hashParams.get('error_code')
      const errorDescription = hashParams.get('error_description')
      
      console.log('Reset password tokens:', { accessToken, type, errorCode })
      
      // Check for errors
      if (errorCode || errorDescription) {
        setLocalError(errorDescription || 'Invalid or expired reset link')
        setIsValidToken(false)
        return
      }
      
      if (accessToken && refreshToken && type === 'recovery') {
        // Set the session with the recovery tokens
        const { data, error } = await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken
        })
        
        if (error) {
          console.error('Error setting recovery session:', error)
          setLocalError('Invalid or expired reset link. Please request a new one.')
          setIsValidToken(false)
        } else {
          console.log('Recovery session established')
          setIsValidToken(true)
        }
      } else {
        setLocalError('Invalid or expired reset link. Please request a new one.')
        setIsValidToken(false)
      }
    } catch (error) {
      console.error('Error checking reset token:', error)
      setLocalError('Invalid or expired reset link. Please request a new one.')
      setIsValidToken(false)
    } finally {
      setCheckingToken(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError('')
    
    // Validation
    if (newPassword !== confirmPassword) {
      setLocalError('Passwords do not match')
      return
    }
    
    if (newPassword.length < 6) {
      setLocalError('Password must be at least 6 characters')
      return
    }
    
    setLoading(true)
    
    try {
      await updatePassword(newPassword)
      // Show success and redirect
      alert('Password updated successfully!')
      navigate('/login')
    } catch (err: any) {
      console.error('Password update error:', err)
      setLocalError(err.message || 'Failed to update password')
    } finally {
      setLoading(false)
    }
  }

  const displayError = localError || error?.message

  if (checkingToken) {
    return (
      <div className="auth-page-container">
        <div className="auth-card">
          <div className="auth-content">
            <p>Verifying reset link...</p>
          </div>
        </div>
      </div>
    )
  }

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
          <h2 className="auth-title">Set new password</h2>
          <p className="auth-subtitle">
            Choose a strong password for your account
          </p>
          
          <RateLimitError error={displayError} />
          
          {isValidToken ? (
            <form onSubmit={handleSubmit} className="auth-form">
              <div className="auth-form-group">
                <label htmlFor="newPassword" className="auth-label">New Password</label>
                <input
                  id="newPassword"
                  type="password"
                  className="auth-input"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  disabled={loading}
                  minLength={6}
                  autoFocus
                />
              </div>
              
              <div className="auth-form-group">
                <label htmlFor="confirmPassword" className="auth-label">Confirm Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  className="auth-input"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={loading}
                  minLength={6}
                />
              </div>
              
              <button type="submit" className="auth-button" disabled={loading}>
                {loading ? <span className="auth-spinner" /> : 'Update Password'}
              </button>
            </form>
          ) : (
            <div style={{ textAlign: 'center', marginTop: '32px' }}>
              <button
                className="auth-button"
                onClick={() => navigate('/forgot-password')}
              >
                Request New Reset Link
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}