import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  Divider,
  Grid,
  Avatar,
  IconButton,
  CircularProgress
} from '@mui/material';
import { Edit as EditIcon, Save as SaveIcon, Cancel as CancelIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const UserProfile: React.FC = () => {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const handleEdit = () => {
    setIsEditing(true);
    setError('');
    setSuccess('');
  };

  const handleCancel = () => {
    setIsEditing(false);
    setFormData({
      name: user?.name || '',
      email: user?.email || '',
    });
    setPasswordData({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');
    setIsSaving(true);

    try {
      // Update user profile
      await axios.put('/api/users/profile', {
        name: formData.name,
        email: formData.email
      });

      // Update password if provided
      if (passwordData.newPassword) {
        if (passwordData.newPassword !== passwordData.confirmPassword) {
          setError('Neue Passwörter stimmen nicht überein');
          setIsSaving(false);
          return;
        }

        await axios.post('/api/users/change-password', {
          current_password: passwordData.currentPassword,
          new_password: passwordData.newPassword
        });
      }

      setSuccess('Profil erfolgreich aktualisiert');
      setIsEditing(false);
      
      // Clear password fields
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Aktualisieren des Profils');
    } finally {
      setIsSaving(false);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  if (!user) return null;

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">Mein Profil</Typography>
          {!isEditing ? (
            <IconButton onClick={handleEdit} color="primary">
              <EditIcon />
            </IconButton>
          ) : (
            <Box>
              <IconButton onClick={handleSave} color="primary" disabled={isSaving}>
                {isSaving ? <CircularProgress size={24} /> : <SaveIcon />}
              </IconButton>
              <IconButton onClick={handleCancel} color="default" disabled={isSaving}>
                <CancelIcon />
              </IconButton>
            </Box>
          )}
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <Box display="flex" alignItems="center" mb={4}>
          <Avatar sx={{ width: 80, height: 80, mr: 3, bgcolor: 'primary.main' }}>
            {getInitials(user.name)}
          </Avatar>
          <Box>
            <Typography variant="h5">{user.name}</Typography>
            <Typography variant="body1" color="text.secondary">{user.email}</Typography>
            <Typography variant="caption" color="text.secondary">
              Mitglied seit {new Date(user.created_at).toLocaleDateString('de-DE')}
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ my: 3 }} />

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField
              fullWidth
              label="Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              disabled={!isEditing || isSaving}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField
              fullWidth
              label="E-Mail"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              disabled={!isEditing || isSaving}
            />
          </Grid>
        </Grid>

        {isEditing && (
          <>
            <Divider sx={{ my: 3 }} />
            <Typography variant="h6" gutterBottom>Passwort ändern</Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Lassen Sie die Felder leer, wenn Sie Ihr Passwort nicht ändern möchten.
            </Typography>
            
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid size={12}>
                <TextField
                  fullWidth
                  label="Aktuelles Passwort"
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                  disabled={isSaving}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Neues Passwort"
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  disabled={isSaving}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Neues Passwort bestätigen"
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  disabled={isSaving}
                />
              </Grid>
            </Grid>
          </>
        )}

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>Organisationen</Typography>
        {user.organizations && user.organizations.length > 0 ? (
          <Box>
            {user.organizations.map((org: any) => (
              <Box key={org.id} sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                <Typography variant="subtitle1">{org.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Rolle: {org.role} • Beigetreten: {new Date(org.created_at).toLocaleDateString('de-DE')}
                </Typography>
              </Box>
            ))}
          </Box>
        ) : (
          <Typography color="text.secondary">Keine Organisationen</Typography>
        )}
      </Paper>
    </Container>
  );
};

export default UserProfile;