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
  Tabs,
  Tab,
} from '@mui/material'
import { Google, GitHub, Apple, Email } from '@mui/icons-material'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import { RateLimitAlert } from './RateLimitAlert'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`auth-tabpanel-${index}`}
      aria-labelledby={`auth-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

export const SupabaseLogin: React.FC = () => {
  const navigate = useNavigate()
  const { signIn, signInWithMagicLink, signInWithGoogle, signInWithGitHub, signInWithApple, error } = useSupabaseAuth()
  
  const [tabValue, setTabValue] = useState(0)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [validationError, setValidationError] = useState('')

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email || !password) {
      setValidationError('Email and password are required')
      return
    }
    
    setValidationError('')
    setLoading(true)
    
    try {
      await signIn(email, password)
      navigate('/dashboard')
    } catch (err: any) {
      console.error('Login error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleMagicLinkLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email) {
      setValidationError('Email is required')
      return
    }
    
    setValidationError('')
    setLoading(true)
    
    try {
      await signInWithMagicLink(email)
      setSuccessMessage('Check your email for the magic link!')
      setEmail('')
    } catch (err: any) {
      console.error('Magic link error:', err)
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

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
    setValidationError('')
    setSuccessMessage('')
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
        <Paper elevation={3} sx={{ width: '100%' }}>
          <Typography component="h1" variant="h5" align="center" sx={{ pt: 3 }}>
            Sign In
          </Typography>
          
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} variant="fullWidth">
              <Tab label="Password" />
              <Tab label="Magic Link" />
            </Tabs>
          </Box>
          
          <RateLimitAlert 
            error={validationError || error?.message} 
            sx={{ mx: 3, mt: 2 }}
          />
          
          {successMessage && (
            <Alert severity="success" sx={{ mx: 3, mt: 2 }}>
              {successMessage}
            </Alert>
          )}
          
          <TabPanel value={tabValue} index={0}>
            <Box component="form" onSubmit={handlePasswordLogin}>
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
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Sign In'}
              </Button>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Link component={RouterLink} to="/forgot-password" variant="body2">
                  Forgot password?
                </Link>
                <Link component={RouterLink} to="/signup" variant="body2">
                  Don't have an account? Sign Up
                </Link>
              </Box>
            </Box>
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <Box component="form" onSubmit={handleMagicLinkLogin}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="magic-email"
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
                startIcon={<Email />}
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Send Magic Link'}
              </Button>
              
              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <Link component={RouterLink} to="/signup" variant="body2">
                  Don't have an account? Sign Up
                </Link>
              </Box>
            </Box>
          </TabPanel>
          
          <Box sx={{ px: 3, pb: 3 }}>
            <Divider sx={{ my: 3 }}>OR</Divider>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<Google />}
                onClick={() => handleOAuthSignIn('google')}
                disabled={loading}
              >
                Continue with Google
              </Button>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<GitHub />}
                onClick={() => handleOAuthSignIn('github')}
                disabled={loading}
              >
                Continue with GitHub
              </Button>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<Apple />}
                onClick={() => handleOAuthSignIn('apple')}
                disabled={loading}
              >
                Continue with Apple
              </Button>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}