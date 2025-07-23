import React, { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { CircularProgress, Box, Typography } from '@mui/material'
import { supabase } from '../../lib/supabase'

export const AuthCallback: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    handleAuthCallback()
  }, [location])

  const handleAuthCallback = async () => {
    try {
      // Log the callback URL for debugging
      console.log('Auth callback URL:', window.location.href)
      console.log('Hash:', location.hash)
      console.log('Search:', location.search)
      
      // First, check for hash fragments (magic links and password resets)
      // These should be handled before OAuth code exchange
      if (location.hash) {
        const hashParams = new URLSearchParams(location.hash.substring(1))
        const accessToken = hashParams.get('access_token')
        const refreshToken = hashParams.get('refresh_token')
        const type = hashParams.get('type')
        const errorCode = hashParams.get('error_code')
        const errorDescription = hashParams.get('error_description')
        
        // Check for errors in the hash
        if (errorCode || errorDescription) {
          console.error('Auth error:', errorCode, errorDescription)
          setError(errorDescription || 'Authentication failed')
          setTimeout(() => navigate('/login'), 3000)
          return
        }
        
        if (type === 'recovery' && accessToken) {
          // Password reset flow - redirect to reset password page with the tokens
          console.log('Password reset flow detected')
          navigate('/reset-password' + location.hash)
          return
        }
        
        if (accessToken && refreshToken) {
          // Magic link or email confirmation flow
          console.log('Setting session from tokens...')
          const { data, error } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken
          })
          
          if (error) {
            console.error('Error setting session:', error)
            setError(error.message)
            setTimeout(() => navigate('/login'), 3000)
            return
          }
          
          console.log('Session established from tokens:', data)
          
          // Wait a moment for the session to be established
          await new Promise(resolve => setTimeout(resolve, 100))
          
          // Redirect immediately after successful magic link auth
          const from = location.state?.from?.pathname || '/'
          console.log('Magic link successful, redirecting to:', from)
          navigate(from, { replace: true })
          return
        }
      }
      
      // Handle OAuth code exchange (for OAuth providers only, not magic links)
      const params = new URLSearchParams(location.search)
      const code = params.get('code')
      
      if (code) {
        console.log('Exchanging OAuth code for session...')
        const { data, error } = await supabase.auth.exchangeCodeForSession(code)
        
        if (error) {
          console.error('Error exchanging code for session:', error)
          setError(error.message)
          setTimeout(() => navigate('/login'), 3000)
          return
        }
        
        console.log('OAuth session established:', data)
      }
      
      // Wait a moment for the session to be established
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // Check if we have a valid session
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()
      
      if (sessionError) {
        console.error('Error getting session:', sessionError)
        setError(sessionError.message)
        setTimeout(() => navigate('/login'), 3000)
        return
      }
      
      if (session) {
        console.log('Session verified, checking MFA...')
        
        // Check if user needs MFA
        const { data: aalData } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel()
        
        if (aalData?.nextLevel === 'aal2' && aalData?.currentLevel !== 'aal2') {
          navigate('/mfa-challenge')
        } else {
          // Get the intended destination or default to home
          const from = location.state?.from?.pathname || '/'
          console.log('Redirecting to:', from)
          navigate(from, { replace: true })
        }
      } else {
        console.log('No session found, redirecting to login...')
        setError('No valid session found')
        setTimeout(() => navigate('/login'), 3000)
      }
    } catch (error) {
      console.error('Auth callback error:', error)
      setError(error instanceof Error ? error.message : 'Authentication failed')
      setTimeout(() => navigate('/login'), 3000)
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
      }}
    >
      {error ? (
        <>
          <Typography variant="h6" color="error" sx={{ mb: 2 }}>
            Authentication Error
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            {error}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Redirecting to login...
          </Typography>
        </>
      ) : (
        <>
          <CircularProgress sx={{ mb: 2 }} />
          <Typography variant="body1" color="text.secondary">
            Completing sign in...
          </Typography>
        </>
      )}
    </Box>
  )
}