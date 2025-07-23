import React, { useEffect } from 'react'
import { Alert, CircularProgress, Box } from '@mui/material'
import { useRateLimitCountdown } from '../../hooks/useRateLimitCountdown'

interface RateLimitAlertProps {
  error: string | null | undefined
  severity?: 'error' | 'warning' | 'info' | 'success'
  sx?: object
  onCountdownComplete?: () => void
}

/**
 * Material-UI Alert component that displays error messages with countdown for rate limit errors
 * Automatically detects rate limit messages and shows a live countdown
 */
export const RateLimitAlert: React.FC<RateLimitAlertProps> = ({
  error,
  severity = 'error',
  sx,
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
      <Alert severity="warning" sx={sx}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircularProgress size={16} thickness={4} />
          {formattedMessage}
        </Box>
      </Alert>
    )
  }

  // Otherwise show the original error
  return (
    <Alert severity={severity} sx={sx}>
      {error}
    </Alert>
  )
}