import React, { useState } from 'react'
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  Link,
  CircularProgress,
} from '@mui/material'
import { ArrowBack } from '@mui/icons-material'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { Link as RouterLink } from 'react-router-dom'
import { RateLimitAlert } from './RateLimitAlert'

export const ForgotPassword: React.FC = () => {
  const { resetPassword, error } = useSupabaseAuth()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [validationError, setValidationError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email) {
      setValidationError('Email is required')
      return
    }
    
    setValidationError('')
    setLoading(true)
    
    try {
      await resetPassword(email)
      setSuccessMessage('Password reset link sent! Check your email.')
      setEmail('')
    } catch (err: any) {
      console.error('Password reset error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
          <Typography component="h1" variant="h5" align="center">
            Reset Password
          </Typography>
          
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
            Enter your email address and we'll send you a link to reset your password.
          </Typography>
          
          <RateLimitAlert 
            error={validationError || error?.message} 
            sx={{ mt: 2 }}
          />
          
          {successMessage && (
            <Alert severity="success" sx={{ mt: 2 }}>
              {successMessage}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Send Reset Link'}
            </Button>
            
            <Box sx={{ textAlign: 'center' }}>
              <Link
                component={RouterLink}
                to="/login"
                variant="body2"
                sx={{ display: 'inline-flex', alignItems: 'center' }}
              >
                <ArrowBack sx={{ mr: 1, fontSize: 18 }} />
                Back to Sign In
              </Link>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}