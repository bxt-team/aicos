import { useState, useEffect, useCallback } from 'react'

interface UseRateLimitCountdownOptions {
  onComplete?: () => void
}

interface UseRateLimitCountdownReturn {
  seconds: number | null
  isActive: boolean
  formattedMessage: string | null
  startCountdown: (errorMessage: string) => void
  reset: () => void
}

/**
 * Hook to handle rate limit error messages with countdown
 * Parses error messages like "For security purposes, you can only request this after 26 seconds"
 * and provides a live countdown
 */
export const useRateLimitCountdown = (
  options: UseRateLimitCountdownOptions = {}
): UseRateLimitCountdownReturn => {
  const { onComplete } = options
  const [seconds, setSeconds] = useState<number | null>(null)
  const [isActive, setIsActive] = useState(false)

  // Parse the error message to extract seconds
  const parseSecondsFromMessage = (message: string): number | null => {
    // Match patterns like "after X seconds", "wait X seconds", "in X seconds"
    const patterns = [
      /after\s+(\d+)\s+seconds?/i,
      /wait\s+(\d+)\s+seconds?/i,
      /in\s+(\d+)\s+seconds?/i,
      /(\d+)\s+seconds?\s+remaining/i,
      /retry\s+in\s+(\d+)\s+seconds?/i,
    ]

    for (const pattern of patterns) {
      const match = message.match(pattern)
      if (match && match[1]) {
        return parseInt(match[1], 10)
      }
    }

    return null
  }

  // Start countdown from error message
  const startCountdown = useCallback((errorMessage: string) => {
    const extractedSeconds = parseSecondsFromMessage(errorMessage)
    
    if (extractedSeconds && extractedSeconds > 0) {
      setSeconds(extractedSeconds)
      setIsActive(true)
    } else {
      setSeconds(null)
      setIsActive(false)
    }
  }, [])

  // Reset countdown
  const reset = useCallback(() => {
    setSeconds(null)
    setIsActive(false)
  }, [])

  // Countdown timer effect
  useEffect(() => {
    if (!isActive || seconds === null || seconds <= 0) {
      if (seconds === 0 && onComplete) {
        onComplete()
      }
      return
    }

    const interval = setInterval(() => {
      setSeconds((prevSeconds) => {
        if (prevSeconds === null || prevSeconds <= 1) {
          setIsActive(false)
          return 0
        }
        return prevSeconds - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [isActive, seconds, onComplete])

  // Format the countdown message
  const formattedMessage = seconds !== null && seconds > 0
    ? `Please wait ${seconds} second${seconds === 1 ? '' : 's'}...`
    : null

  return {
    seconds,
    isActive,
    formattedMessage,
    startCountdown,
    reset,
  }
}