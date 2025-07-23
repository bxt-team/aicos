import React, { useState } from 'react'
import { RateLimitError } from './RateLimitError'
import '../../styles/auth-branded.css'

/**
 * Demo component to test RateLimitError with different error messages
 * This can be used for development/testing purposes
 */
export const RateLimitErrorDemo: React.FC = () => {
  const [currentError, setCurrentError] = useState<string | null>(null)

  const sampleErrors = [
    "For security purposes, you can only request this after 26 seconds",
    "Too many requests. Please wait 60 seconds before trying again.",
    "Rate limit exceeded. Retry in 30 seconds.",
    "Please wait 15 seconds before requesting another magic link.",
    "You can request a password reset in 45 seconds.",
    "Invalid credentials", // Non-rate limit error
    "Network error occurred", // Non-rate limit error
  ]

  return (
    <div className="auth-page-container">
      <div className="auth-card">
        <div className="auth-content">
          <h2 className="auth-title">Rate Limit Error Demo</h2>
          <p className="auth-subtitle">Click on different error messages to see the countdown in action</p>
          
          <div style={{ marginTop: '24px', marginBottom: '24px' }}>
            <RateLimitError 
              error={currentError} 
              onCountdownComplete={() => {
                console.log('Countdown completed!')
                setCurrentError(null)
              }}
            />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {sampleErrors.map((error, index) => (
              <button
                key={index}
                className="auth-button"
                onClick={() => setCurrentError(error)}
                style={{ fontSize: '14px', padding: '8px 16px' }}
              >
                {error}
              </button>
            ))}
            
            <button
              className="auth-button"
              onClick={() => setCurrentError(null)}
              style={{ 
                fontSize: '14px', 
                padding: '8px 16px',
                backgroundColor: 'var(--aicos-danger)',
                marginTop: '12px'
              }}
            >
              Clear Error
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}