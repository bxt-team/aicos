import React, { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { CircularProgress, Box, Typography } from '@mui/material'
import { supabase } from '../../lib/supabase'

export const AuthCallback: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    handleAuthCallback()
  }, [])

  const handleAuthCallback = async () => {
    try {
      // Get the code from the URL
      const params = new URLSearchParams(location.search)
      const code = params.get('code')
      
      if (code) {
        // Exchange the code for a session
        const { data, error } = await supabase.auth.exchangeCodeForSession(code)
        
        if (error) {
          console.error('Error exchanging code for session:', error)
          navigate('/login')
          return
        }
      }
      
      // Check if we have a hash fragment (for magic links and password resets)
      if (location.hash) {
        const hashParams = new URLSearchParams(location.hash.substring(1))
        const accessToken = hashParams.get('access_token')
        const type = hashParams.get('type')
        
        if (type === 'recovery') {
          // Password reset flow
          navigate('/reset-password' + location.hash)
          return
        }
      }
      
      // Check if user needs MFA
      const { data: { session } } = await supabase.auth.getSession()
      if (session) {
        const { data: aalData } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel()
        
        if (aalData?.nextLevel === 'aal2' && aalData?.currentLevel !== 'aal2') {
          navigate('/mfa-challenge')
        } else {
          // Get the intended destination or default to dashboard
          const from = location.state?.from?.pathname || '/dashboard'
          navigate(from, { replace: true })
        }
      } else {
        navigate('/login')
      }
    } catch (error) {
      console.error('Auth callback error:', error)
      navigate('/login')
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
      <CircularProgress sx={{ mb: 2 }} />
      <Typography variant="body1" color="text.secondary">
        Completing sign in...
      </Typography>
    </Box>
  )
}