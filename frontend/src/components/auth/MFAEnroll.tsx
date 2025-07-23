import React, { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  TextField,
  Alert,
  CircularProgress,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
} from '@mui/material'
import { QrCode, Delete, Verified, CheckCircle } from '@mui/icons-material'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'

interface MFAEnrollProps {
  open: boolean
  onClose: () => void
}

export const MFAEnroll: React.FC<MFAEnrollProps> = ({ open, onClose }) => {
  const { enrollMFA, verifyMFA, unenrollMFA, listMFAFactors } = useSupabaseAuth()
  
  const [step, setStep] = useState<'list' | 'enroll' | 'verify'>('list')
  const [qrCode, setQrCode] = useState('')
  const [secret, setSecret] = useState('')
  const [factorId, setFactorId] = useState('')
  const [verifyCode, setVerifyCode] = useState('')
  const [factors, setFactors] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      loadFactors()
    }
  }, [open])

  const loadFactors = async () => {
    try {
      const factorsList = await listMFAFactors()
      setFactors(factorsList)
    } catch (err) {
      console.error('Error loading factors:', err)
    }
  }

  const handleEnroll = async () => {
    setLoading(true)
    setError('')
    
    try {
      const { qr, secret, factorId } = await enrollMFA()
      setQrCode(qr)
      setSecret(secret)
      setFactorId(factorId)
      setStep('enroll')
    } catch (err: any) {
      setError(err.message || 'Failed to enroll MFA')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async () => {
    if (!verifyCode || verifyCode.length !== 6) {
      setError('Please enter a 6-digit code')
      return
    }
    
    setLoading(true)
    setError('')
    
    try {
      await verifyMFA(factorId, verifyCode)
      setStep('list')
      setVerifyCode('')
      loadFactors()
    } catch (err: any) {
      setError(err.message || 'Invalid code')
    } finally {
      setLoading(false)
    }
  }

  const handleUnenroll = async (factorId: string) => {
    if (!window.confirm('Are you sure you want to remove this 2FA method?')) {
      return
    }
    
    setLoading(true)
    try {
      await unenrollMFA(factorId)
      loadFactors()
    } catch (err: any) {
      setError(err.message || 'Failed to remove 2FA')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setStep('list')
    setQrCode('')
    setSecret('')
    setFactorId('')
    setVerifyCode('')
    setError('')
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {step === 'list' && 'Two-Factor Authentication'}
        {step === 'enroll' && 'Set Up Authenticator App'}
        {step === 'verify' && 'Verify Authenticator'}
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {step === 'list' && (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Add an extra layer of security to your account by enabling two-factor authentication.
            </Typography>
            
            {factors.length > 0 && (
              <Paper variant="outlined" sx={{ mb: 2 }}>
                <List>
                  {factors.map((factor) => (
                    <ListItem key={factor.id}>
                      <ListItemText
                        primary={factor.friendly_name || 'Authenticator App'}
                        secondary={`Added on ${new Date(factor.created_at).toLocaleDateString()}`}
                      />
                      <ListItemSecondaryAction>
                        <Chip
                          icon={<Verified />}
                          label={factor.status}
                          color="success"
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        <IconButton
                          edge="end"
                          onClick={() => handleUnenroll(factor.id)}
                          disabled={loading}
                        >
                          <Delete />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </Paper>
            )}
            
            <Button
              fullWidth
              variant="contained"
              startIcon={<QrCode />}
              onClick={handleEnroll}
              disabled={loading}
            >
              Add Authenticator App
            </Button>
          </>
        )}
        
        {step === 'enroll' && (
          <>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Scan this QR code with your authenticator app (Google Authenticator, 1Password, etc.)
            </Typography>
            
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <img
                src={qrCode}
                alt="QR Code"
                style={{ maxWidth: '100%', height: 'auto' }}
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Can't scan? Enter this code manually:
            </Typography>
            
            <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
              <Typography
                variant="body2"
                sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}
              >
                {secret}
              </Typography>
            </Paper>
            
            <Button
              fullWidth
              variant="contained"
              onClick={() => setStep('verify')}
            >
              Next: Verify
            </Button>
          </>
        )}
        
        {step === 'verify' && (
          <>
            <Typography variant="body2" sx={{ mb: 3 }}>
              Enter the 6-digit code from your authenticator app to complete setup.
            </Typography>
            
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
              sx={{ mb: 3 }}
            />
            
            <Button
              fullWidth
              variant="contained"
              onClick={handleVerify}
              disabled={loading || verifyCode.length !== 6}
              startIcon={loading ? <CircularProgress size={20} /> : <CheckCircle />}
            >
              {loading ? 'Verifying...' : 'Verify and Enable'}
            </Button>
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose}>
          {step === 'list' ? 'Close' : 'Cancel'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}