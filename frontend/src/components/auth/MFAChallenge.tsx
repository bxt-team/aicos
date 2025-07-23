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
import { Lock } from '@mui/icons-material'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { useNavigate } from 'react-router-dom'

export const MFAChallenge: React.FC = () => {
  const navigate = useNavigate()
  const { verifyMFA, listMFAFactors, getAAL } = useSupabaseAuth()
  
  const [verifyCode, setVerifyCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [factorId, setFactorId] = useState('')

  useEffect(() => {
    checkMFAStatus()
  }, [])

  const checkMFAStatus = async () => {
    try {
      // Check if MFA is required
      const { currentLevel, nextLevel } = await getAAL()
      
      if (currentLevel === 'aal2' || nextLevel !== 'aal2') {
        // MFA not required or already completed
        navigate('/dashboard')
        return
      }
      
      // Get the user's MFA factors
      const factors = await listMFAFactors()
      if (factors.length === 0) {
        // No MFA factors enrolled
        navigate('/dashboard')
        return
      }
      
      // Use the first TOTP factor
      const totpFactor = factors.find(f => f.factor_type === 'totp')
      if (totpFactor) {
        setFactorId(totpFactor.id)
      }
    } catch (err) {
      console.error('Error checking MFA status:', err)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!verifyCode || verifyCode.length !== 6) {
      setError('Please enter a 6-digit code')
      return
    }
    
    setLoading(true)
    setError('')
    
    try {
      await verifyMFA(factorId, verifyCode)
      // MFA successful, navigate to dashboard
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Invalid code')
      setVerifyCode('')
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
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Lock sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography component="h1" variant="h5">
              Two-Factor Authentication
            </Typography>
          </Box>
          
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
            Enter the 6-digit code from your authenticator app
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Verification Code"
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              inputProps={{
                maxLength: 6,
                style: { textAlign: 'center', fontSize: '1.5rem', letterSpacing: '0.5rem' }
              }}
              disabled={loading}
              autoFocus
              sx={{ mb: 3 }}
            />
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading || verifyCode.length !== 6}
            >
              {loading ? <CircularProgress size={24} /> : 'Verify'}
            </Button>
            
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Lost access to your authenticator?
              </Typography>
              <Button
                variant="text"
                size="small"
                onClick={() => navigate('/account-recovery')}
              >
                Use recovery options
              </Button>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}