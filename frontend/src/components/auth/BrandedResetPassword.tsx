import React, { useState, useEffect } from 'react'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { useNavigate, useLocation } from 'react-router-dom'
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

  useEffect(() => {
    // Apply auth page class to body
    document.body.classList.add('auth-page')
    
    // Check if we have a valid reset token in the URL
    const hashParams = new URLSearchParams(location.hash.substring(1))
    const accessToken = hashParams.get('access_token')
    const type = hashParams.get('type')
    
    if (accessToken && type === 'recovery') {
      setIsValidToken(true)
    } else {
      setLocalError('Invalid or expired reset link. Please request a new one.')
    }
    
    return () => {
      document.body.classList.remove('auth-page')
    }
  }, [location])

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
      setLocalError(err.message || 'Failed to update password')
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
            <p className="auth-brand-tagline">AI Content Operating System</p>
          </div>
        </div>
        
        <div className="auth-content">
          <h2 className="auth-title">Set new password</h2>
          <p className="auth-subtitle">
            Choose a strong password for your account
          </p>
          
          {displayError && (
            <div className="auth-error">
              {displayError}
            </div>
          )}
          
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