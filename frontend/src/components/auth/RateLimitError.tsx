import React, { useEffect } from 'react'
import { useRateLimitCountdown } from '../../hooks/useRateLimitCountdown'

interface RateLimitErrorProps {
  error: string | null | undefined
  className?: string
  onCountdownComplete?: () => void
}

/**
 * Component that displays error messages with countdown for rate limit errors
 * Automatically detects rate limit messages and shows a live countdown
 */
export const RateLimitError: React.FC<RateLimitErrorProps> = ({
  error,
  className = 'auth-error',
  onCountdownComplete,
}) => {
  const { formattedMessage, startCountdown, reset, isActive } = useRateLimitCountdown({
    onComplete: onCountdownComplete,
  })

  useEffect(() => {
    if (error) {
      startCountdown(error)
    } else {
      reset()
    }
  }, [error, startCountdown, reset])

  if (!error) return null

  // If it's a rate limit error with active countdown, show the countdown
  if (isActive && formattedMessage) {
    return (
      <div className={className}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="auth-spinner" style={{ width: '16px', height: '16px' }} />
          {formattedMessage}
        </div>
      </div>
    )
  }

  // Otherwise show the original error
  return <div className={className}>{error}</div>
}