import React, { useEffect, useState } from 'react'
import { Box, Paper, Typography, Button, Divider } from '@mui/material'
import { supabase } from '../../lib/supabase'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'

export const AuthDebug: React.FC = () => {
  const { user, session } = useSupabaseAuth()
  const [authConfig, setAuthConfig] = useState<any>(null)
  const [testResult, setTestResult] = useState<string>('')

  useEffect(() => {
    checkAuthConfig()
  }, [])

  const checkAuthConfig = async () => {
    const config = {
      supabaseUrl: process.env.REACT_APP_SUPABASE_URL,
      supabaseAnonKey: process.env.REACT_APP_SUPABASE_ANON_KEY ? 'Set (hidden)' : 'Not set',
      currentUrl: window.location.origin,
      authCallbackUrl: `${window.location.origin}/auth/callback`,
      resetPasswordUrl: `${window.location.origin}/reset-password`,
    }
    setAuthConfig(config)
  }

  const testMagicLink = async () => {
    const testEmail = prompt('Enter email for magic link test:')
    if (!testEmail) return

    try {
      const { data, error } = await supabase.auth.signInWithOtp({
        email: testEmail,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      
      if (error) {
        setTestResult(`Magic link error: ${error.message}`)
      } else {
        setTestResult(`Magic link sent to ${testEmail}. Check your email and the browser console when clicking the link.`)
      }
    } catch (err) {
      setTestResult(`Exception: ${err}`)
    }
  }

  const testPasswordReset = async () => {
    const testEmail = prompt('Enter email for password reset test:')
    if (!testEmail) return

    try {
      const { data, error } = await supabase.auth.resetPasswordForEmail(testEmail, {
        redirectTo: `${window.location.origin}/reset-password`,
      })
      
      if (error) {
        setTestResult(`Password reset error: ${error.message}`)
      } else {
        setTestResult(`Password reset email sent to ${testEmail}. Check your email and the browser console when clicking the link.`)
      }
    } catch (err) {
      setTestResult(`Exception: ${err}`)
    }
  }

  const clearSession = async () => {
    await supabase.auth.signOut()
    localStorage.clear()
    sessionStorage.clear()
    window.location.reload()
  }

  return (
    <Paper sx={{ p: 3, maxWidth: 800, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Auth Debug Information
      </Typography>
      
      <Divider sx={{ my: 2 }} />
      
      <Typography variant="h6" gutterBottom>
        Current Session
      </Typography>
      <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        <Typography variant="body2">
          User: {user ? user.email : 'No user logged in'}
        </Typography>
        <Typography variant="body2">
          Session: {session ? 'Active' : 'No session'}
        </Typography>
        {session && (
          <Typography variant="body2">
            Expires: {new Date(session.expires_at! * 1000).toLocaleString()}
          </Typography>
        )}
      </Box>
      
      <Divider sx={{ my: 2 }} />
      
      <Typography variant="h6" gutterBottom>
        Configuration
      </Typography>
      <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        {authConfig && Object.entries(authConfig).map(([key, value]) => (
          <Typography key={key} variant="body2">
            {key}: {String(value)}
          </Typography>
        ))}
      </Box>
      
      <Divider sx={{ my: 2 }} />
      
      <Typography variant="h6" gutterBottom>
        Test Auth Flows
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <Button variant="contained" onClick={testMagicLink}>
          Test Magic Link
        </Button>
        <Button variant="contained" onClick={testPasswordReset}>
          Test Password Reset
        </Button>
        <Button variant="contained" color="error" onClick={clearSession}>
          Clear All Sessions
        </Button>
      </Box>
      
      {testResult && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
          <Typography variant="body2">{testResult}</Typography>
        </Box>
      )}
      
      <Divider sx={{ my: 2 }} />
      
      <Typography variant="h6" gutterBottom>
        Important Notes
      </Typography>
      <Box sx={{ p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
        <Typography variant="body2" paragraph>
          1. Make sure these URLs are added to your Supabase project's allowed redirect URLs:
        </Typography>
        <Typography variant="body2" component="ul">
          <li>{window.location.origin}/auth/callback</li>
          <li>{window.location.origin}/reset-password</li>
          <li>{window.location.origin}</li>
        </Typography>
        <Typography variant="body2" paragraph>
          2. Check the browser console for detailed logs when clicking email links.
        </Typography>
        <Typography variant="body2">
          3. Email link tokens are single-use. If you click a link twice, it will fail.
        </Typography>
      </Box>
    </Paper>
  )
}