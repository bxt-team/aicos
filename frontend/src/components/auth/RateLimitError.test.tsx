import React from 'react'
import { render, screen, act } from '@testing-library/react'
import { RateLimitError } from './RateLimitError'

// Mock the useRateLimitCountdown hook
jest.mock('../../hooks/useRateLimitCountdown', () => ({
  useRateLimitCountdown: jest.fn(),
}))

import { useRateLimitCountdown } from '../../hooks/useRateLimitCountdown'

describe('RateLimitError', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('shows countdown for rate limit errors', () => {
    const mockHook = useRateLimitCountdown as jest.Mock
    mockHook.mockReturnValue({
      formattedMessage: 'Please wait 25 seconds...',
      startCountdown: jest.fn(),
      reset: jest.fn(),
      isActive: true,
    })

    render(
      <RateLimitError 
        error="For security purposes, you can only request this after 26 seconds" 
      />
    )

    expect(screen.getByText('Please wait 25 seconds...')).toBeInTheDocument()
  })

  it('shows original error for non-rate limit errors', () => {
    const mockHook = useRateLimitCountdown as jest.Mock
    mockHook.mockReturnValue({
      formattedMessage: null,
      startCountdown: jest.fn(),
      reset: jest.fn(),
      isActive: false,
    })

    render(
      <RateLimitError 
        error="Invalid credentials" 
      />
    )

    expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
  })

  it('renders nothing when error is null', () => {
    const mockHook = useRateLimitCountdown as jest.Mock
    mockHook.mockReturnValue({
      formattedMessage: null,
      startCountdown: jest.fn(),
      reset: jest.fn(),
      isActive: false,
    })

    const { container } = render(<RateLimitError error={null} />)
    
    expect(container.firstChild).toBeNull()
  })
})