import React, { useState } from 'react'
import {
  Container,
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  Button,
  TextField,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material'
import {
  Security,
  Email,
  Password,
  Delete,
  Add,
  Google,
  GitHub,
  Apple,
} from '@mui/icons-material'
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext'
import { MFAEnroll } from './MFAEnroll'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

export const AccountSettings: React.FC = () => {
  const { user, updatePassword, signOut } = useSupabaseAuth()
  const [tabValue, setTabValue] = useState(0)
  const [mfaDialogOpen, setMfaDialogOpen] = useState(false)
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handlePasswordChange = async () => {
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }
    
    try {
      await updatePassword(newPassword)
      setSuccess('Password updated successfully')
      setPasswordDialogOpen(false)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err: any) {
      setError(err.message || 'Failed to update password')
    }
  }

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'google':
        return <Google />
      case 'github':
        return <GitHub />
      case 'apple':
        return <Apple />
      case 'email':
        return <Email />
      default:
        return null
    }
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Profile" />
            <Tab label="Security" />
            <Tab label="Connected Accounts" />
          </Tabs>
        </Box>
        
        {success && (
          <Alert severity="success" onClose={() => setSuccess('')} sx={{ m: 2 }}>
            {success}
          </Alert>
        )}
        
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Profile Information
          </Typography>
          <List>
            <ListItem>
              <ListItemText
                primary="Email"
                secondary={user?.email}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="User ID"
                secondary={user?.id}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Account Created"
                secondary={user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              />
            </ListItem>
          </List>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Security Settings
          </Typography>
          
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Password
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Password />}
              onClick={() => setPasswordDialogOpen(true)}
            >
              Change Password
            </Button>
          </Box>
          
          <Divider sx={{ my: 3 }} />
          
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Two-Factor Authentication
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Add an extra layer of security to your account
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Security />}
              onClick={() => setMfaDialogOpen(true)}
            >
              Manage 2FA
            </Button>
          </Box>
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Connected Accounts
          </Typography>
          <List>
            {user?.app_metadata?.providers?.map((provider: string) => (
              <ListItem key={provider}>
                <ListItemText
                  primary={provider.charAt(0).toUpperCase() + provider.slice(1)}
                  secondary="Connected"
                />
                <ListItemSecondaryAction>
                  {getProviderIcon(provider)}
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Connect additional accounts for easier sign in
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              {!user?.app_metadata?.providers?.includes('google') && (
                <Button
                  variant="outlined"
                  startIcon={<Google />}
                  size="small"
                >
                  Connect Google
                </Button>
              )}
              {!user?.app_metadata?.providers?.includes('github') && (
                <Button
                  variant="outlined"
                  startIcon={<GitHub />}
                  size="small"
                >
                  Connect GitHub
                </Button>
              )}
              {!user?.app_metadata?.providers?.includes('apple') && (
                <Button
                  variant="outlined"
                  startIcon={<Apple />}
                  size="small"
                >
                  Connect Apple
                </Button>
              )}
            </Box>
          </Box>
        </TabPanel>
        
        <Box sx={{ p: 3, borderTop: 1, borderColor: 'divider' }}>
          <Button
            variant="outlined"
            color="error"
            onClick={() => signOut()}
          >
            Sign Out
          </Button>
        </Box>
      </Paper>
      
      <MFAEnroll open={mfaDialogOpen} onClose={() => setMfaDialogOpen(false)} />
      
      <Dialog open={passwordDialogOpen} onClose={() => setPasswordDialogOpen(false)}>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            fullWidth
            margin="normal"
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <TextField
            fullWidth
            margin="normal"
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordDialogOpen(false)}>Cancel</Button>
          <Button onClick={handlePasswordChange} variant="contained">
            Update Password
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}