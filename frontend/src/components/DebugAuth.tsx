import React from 'react';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { Card, CardContent, Typography, Box, Chip, Button } from '@mui/material';

const DebugAuth: React.FC = () => {
  const { user, loading } = useSupabaseAuth();
  // TODO: Add organization support later
  const currentOrganization: any = null;
  const currentProject: any = null;

  const handleClearLocalStorage = () => {
    localStorage.removeItem('currentOrganizationId');
    localStorage.removeItem('currentProjectId');
    window.location.reload();
  };

  const handleClearAll = () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.reload();
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Auth Debug Info</Typography>
      
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Loading State</Typography>
          <Chip label={loading ? 'Loading...' : 'Loaded'} color={loading ? 'warning' : 'success'} />
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>User Info</Typography>
          {user ? (
            <>
              <Typography>ID: {user.id}</Typography>
              <Typography>Email: {user.email}</Typography>
              <Typography>Name: {user.user_metadata?.name || 'Not set'}</Typography>
              <Typography>Provider: {user.app_metadata?.provider || 'email'}</Typography>
              <Typography>Created: {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</Typography>
            </>
          ) : (
            <Typography color="text.secondary">No user logged in</Typography>
          )}
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Current Organization</Typography>
          {currentOrganization ? (
            <>
              <Typography>ID: {currentOrganization.id}</Typography>
              <Typography>Name: {currentOrganization.name}</Typography>
              <Typography>Role: {currentOrganization.role}</Typography>
            </>
          ) : (
            <Typography color="text.secondary">No organization selected</Typography>
          )}
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Current Project</Typography>
          {currentProject ? (
            <>
              <Typography>ID: {currentProject.id}</Typography>
              <Typography>Name: {currentProject.name}</Typography>
              <Typography>Description: {currentProject.description || 'No description'}</Typography>
              <Typography>Organization ID: {currentProject.organization_id}</Typography>
              <Typography>Created: {new Date(currentProject.created_at).toLocaleString()}</Typography>
            </>
          ) : (
            <Typography color="text.secondary">No project selected</Typography>
          )}
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Local Storage</Typography>
          <Typography variant="body2">
            Organization ID: {localStorage.getItem('currentOrganizationId') || 'Not set'}
          </Typography>
          <Typography variant="body2">
            Project ID: {localStorage.getItem('currentProjectId') || 'Not set'}
          </Typography>
          <Typography variant="body2">
            Access Token: {localStorage.getItem('accessToken') ? 'Present' : 'Not present'}
          </Typography>
        </CardContent>
      </Card>

      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button variant="outlined" onClick={handleClearLocalStorage}>
          Clear Org/Project Selection
        </Button>
        <Button variant="outlined" color="warning" onClick={handleClearAll}>
          Clear All Storage (Logout)
        </Button>
      </Box>
    </Box>
  );
};

export default DebugAuth;