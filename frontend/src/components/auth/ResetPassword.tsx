import React, { useState, useEffect } from 'react'
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { useNavigate, useLocation } from 'react-router-dom'

export const ResetPassword: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { updatePassword, error } = useSupabaseAuth()
  
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [validationError, setValidationError] = useState('')
  const [isValidToken, setIsValidToken] = useState(false)

  useEffect(() => {
    // Check if we have a valid reset token in the URL
    const hashParams = new URLSearchParams(location.hash.substring(1))
    const accessToken = hashParams.get('access_token')
    const type = hashParams.get('type')
    
    if (accessToken && type === 'recovery') {
      setIsValidToken(true)
    } else {
      setValidationError('Invalid or expired reset link. Please request a new one.')
    }
  }, [location])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validation
    if (!newPassword || !confirmPassword) {
      setValidationError('All fields are required')
      return
    }
    
    if (newPassword !== confirmPassword) {
      setValidationError('Passwords do not match')
      return
    }
    
    if (newPassword.length < 6) {
      setValidationError('Password must be at least 6 characters')
      return
    }
    
    setValidationError('')
    setLoading(true)
    
    try {
      await updatePassword(newPassword)
      // Show success and redirect
      alert('Password updated successfully!')
      navigate('/login')
    } catch (err: any) {
      console.error('Password update error:', err)
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
            Set New Password
          </Typography>
          
          {(error || validationError) && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {validationError || error?.message}
            </Alert>
          )}
          
          {isValidToken ? (
            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
              <TextField
                margin="normal"
                required
                fullWidth
                name="newPassword"
                label="New Password"
                type="password"
                id="newPassword"
                autoComplete="new-password"
                autoFocus
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={loading}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="confirmPassword"
                label="Confirm New Password"
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
                {loading ? <CircularProgress size={24} /> : 'Update Password'}
              </Button>
            </Box>
          ) : (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Button
                variant="contained"
                onClick={() => navigate('/forgot-password')}
              >
                Request New Reset Link
              </Button>
            </Box>
          )}
        </Paper>
      </Box>
    </Container>
  )
}