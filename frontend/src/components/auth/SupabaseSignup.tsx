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
  Divider,
  CircularProgress,
} from '@mui/material'
import { Google, GitHub, Apple } from '@mui/icons-material'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import { RateLimitAlert } from './RateLimitAlert'

export const SupabaseSignup: React.FC = () => {
  const navigate = useNavigate()
  const { signUp, signInWithGoogle, signInWithGitHub, signInWithApple, error } = useSupabaseAuth()
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [validationError, setValidationError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validation
    if (!email || !password || !confirmPassword) {
      setValidationError('All fields are required')
      return
    }
    
    if (password !== confirmPassword) {
      setValidationError('Passwords do not match')
      return
    }
    
    if (password.length < 6) {
      setValidationError('Password must be at least 6 characters')
      return
    }
    
    setValidationError('')
    setLoading(true)
    
    try {
      await signUp(email, password)
      setSuccessMessage('Account created! Check your email to confirm your account.')
      // Clear form
      setEmail('')
      setPassword('')
      setConfirmPassword('')
    } catch (err: any) {
      console.error('Signup error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleOAuthSignIn = async (provider: 'google' | 'github' | 'apple') => {
    setLoading(true)
    try {
      switch (provider) {
        case 'google':
          await signInWithGoogle()
          break
        case 'github':
          await signInWithGitHub()
          break
        case 'apple':
          await signInWithApple()
          break
      }
    } catch (err) {
      console.error(`${provider} sign in error:`, err)
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
            Create Account
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
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Confirm Password"
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Sign Up'}
            </Button>
            
            <Box sx={{ mt: 2 }}>
              <Link component={RouterLink} to="/login" variant="body2">
                Already have an account? Sign In
              </Link>
            </Box>
            
            <Divider sx={{ my: 3 }}>OR</Divider>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<Google />}
                onClick={() => handleOAuthSignIn('google')}
                disabled={loading}
              >
                Sign up with Google
              </Button>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<GitHub />}
                onClick={() => handleOAuthSignIn('github')}
                disabled={loading}
              >
                Sign up with GitHub
              </Button>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<Apple />}
                onClick={() => handleOAuthSignIn('apple')}
                disabled={loading}
              >
                Sign up with Apple
              </Button>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}