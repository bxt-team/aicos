import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Avatar,
  Divider
} from '@mui/material';
import Grid2 from '@mui/material/Grid2';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  CalendarToday as CalendarIcon,
  Verified as VerifiedIcon
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';

const UserProfile: React.FC = () => {
  const { user, loading: authLoading } = useSupabaseAuth();
  const { organizations, currentOrganization } = useOrganization();
  
  if (authLoading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }
  
  if (!user) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">No user logged in</Alert>
      </Container>
    );
  }
  
  const getInitials = (email: string) => {
    return email.substring(0, 2).toUpperCase();
  };
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };
  
  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
          <Avatar
            sx={{
              width: 80,
              height: 80,
              bgcolor: 'primary.main',
              fontSize: '1.5rem',
              mr: 3
            }}
          >
            {user.email ? getInitials(user.email) : <PersonIcon />}
          </Avatar>
          <Box>
            <Typography variant="h4" gutterBottom>
              {user.user_metadata?.name || user.email?.split('@')[0] || 'User'}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {user.email}
            </Typography>
          </Box>
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Grid2 container spacing={3}>
          <Grid2 size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Email
                </Typography>
                <Typography variant="body1">
                  {user.email}
                </Typography>
              </Box>
            </Box>
          </Grid2>
          
          <Grid2 size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <VerifiedIcon sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Email Verified
                </Typography>
                <Typography variant="body1">
                  {user.email_confirmed_at ? 'Yes' : 'No'}
                </Typography>
              </Box>
            </Box>
          </Grid2>
          
          <Grid2 size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CalendarIcon sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Account Created
                </Typography>
                <Typography variant="body1">
                  {formatDate(user.created_at)}
                </Typography>
              </Box>
            </Box>
          </Grid2>
          
          <Grid2 size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <PersonIcon sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  User ID
                </Typography>
                <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                  {user.id}
                </Typography>
              </Box>
            </Box>
          </Grid2>
        </Grid2>
        
        <Divider sx={{ my: 3 }} />
        
        <Typography variant="h6" gutterBottom>
          Organizations
        </Typography>
        
        {organizations.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No organizations yet
          </Typography>
        ) : (
          <Box sx={{ mt: 2 }}>
            {organizations.map(org => (
              <Box
                key={org.id}
                sx={{
                  p: 2,
                  mb: 1,
                  bgcolor: currentOrganization?.id === org.id ? 'action.selected' : 'background.default',
                  borderRadius: 1,
                  border: '1px solid',
                  borderColor: 'divider'
                }}
              >
                <Typography variant="subtitle1">
                  {org.name}
                  {currentOrganization?.id === org.id && (
                    <Typography component="span" variant="caption" sx={{ ml: 1, color: 'primary.main' }}>
                      (Current)
                    </Typography>
                  )}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {org.description || 'No description'}
                </Typography>
              </Box>
            ))}
          </Box>
        )}
        
        {user.user_metadata && Object.keys(user.user_metadata).length > 0 && (
          <>
            <Divider sx={{ my: 3 }} />
            <Typography variant="h6" gutterBottom>
              User Metadata
            </Typography>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                {JSON.stringify(user.user_metadata, null, 2)}
              </pre>
            </Box>
          </>
        )}
      </Paper>
    </Container>
  );
};

export default UserProfile;