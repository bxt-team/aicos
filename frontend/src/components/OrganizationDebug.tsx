import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  TextField,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Divider,
  Chip
} from '@mui/material';
import { useOrganization } from '../contexts/OrganizationContext';
import api, { apiService } from '../services/api';

const OrganizationDebug: React.FC = () => {
  const { currentOrganization } = useOrganization();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [testResults, setTestResults] = useState<any>(null);
  const [debugResults, setDebugResults] = useState<any>(null);
  const [customOrgId, setCustomOrgId] = useState('');

  const orgId = customOrgId || currentOrganization?.id || '';

  const runTestMembers = async () => {
    if (!orgId) {
      setError('Please enter an organization ID');
      return;
    }

    setLoading(true);
    setError('');
    setTestResults(null);

    try {
      const response = await api.get(`/api/organizations/${orgId}/test-members`);
      setTestResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to run test');
      console.error('Test members error:', err.response || err);
    } finally {
      setLoading(false);
    }
  };

  const runDebugMembership = async () => {
    if (!orgId) {
      setError('Please enter an organization ID');
      return;
    }

    setLoading(true);
    setError('');
    setDebugResults(null);

    try {
      const response = await api.get(`/api/organizations/${orgId}/debug-membership`);
      setDebugResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to run debug');
      console.error('Debug membership error:', err.response || err);
    } finally {
      setLoading(false);
    }
  };

  const testMembersEndpoint = async () => {
    if (!orgId) {
      setError('Please enter an organization ID');
      return;
    }

    setLoading(true);
    setError('');

    try {
      console.log('[Debug] Testing members endpoint for org:', orgId);
      const response = await apiService.organizations.getMembers(orgId);
      console.log('[Debug] Members response:', response);
      setTestResults({
        endpoint: '/api/organizations/{id}/members',
        status: 'success',
        data: response.data
      });
    } catch (err: any) {
      console.error('[Debug] Members endpoint error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load members');
      setTestResults({
        endpoint: '/api/organizations/{id}/members',
        status: 'error',
        error: err.response?.data || err.message,
        statusCode: err.response?.status
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Organization Debug Tools
        </Typography>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          Use these tools to debug organization membership issues
        </Alert>

        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="Organization ID"
            value={customOrgId}
            onChange={(e) => setCustomOrgId(e.target.value)}
            placeholder={currentOrganization?.id || 'Enter organization ID'}
            helperText={currentOrganization ? `Current org: ${currentOrganization.name} (${currentOrganization.id})` : 'No organization selected'}
            sx={{ mb: 2 }}
          />
          
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Testing organization: <strong>{orgId || 'None'}</strong>
          </Typography>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            onClick={runTestMembers}
            disabled={loading || !orgId}
          >
            Test Members Query
          </Button>
          
          <Button
            variant="contained"
            color="secondary"
            onClick={runDebugMembership}
            disabled={loading || !orgId}
          >
            Debug Membership
          </Button>
          
          <Button
            variant="contained"
            color="info"
            onClick={testMembersEndpoint}
            disabled={loading || !orgId}
          >
            Test Members API Endpoint
          </Button>
        </Box>

        {loading && <CircularProgress />}

        {testResults && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Test Results
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <pre style={{ 
                overflow: 'auto', 
                backgroundColor: '#f5f5f5', 
                padding: '16px',
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                {JSON.stringify(testResults, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}

        {debugResults && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Debug Results
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {debugResults.auth_user && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Auth User
                  </Typography>
                  <Typography variant="body2">
                    ID: {debugResults.auth_user.id}
                  </Typography>
                  <Typography variant="body2">
                    Email: {debugResults.auth_user.email}
                  </Typography>
                </Box>
              )}

              {debugResults.public_user && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Public User
                  </Typography>
                  <Typography variant="body2">
                    ID: {debugResults.public_user.id}
                  </Typography>
                  <Typography variant="body2">
                    Email: {debugResults.public_user.email}
                  </Typography>
                </Box>
              )}

              {debugResults.membership && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Your Membership
                  </Typography>
                  <Typography variant="body2">
                    Role: <Chip label={debugResults.membership.role} size="small" color="primary" />
                  </Typography>
                  <Typography variant="body2">
                    Joined: {new Date(debugResults.membership.created_at).toLocaleDateString()}
                  </Typography>
                </Box>
              )}

              {debugResults.debug_info && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Debug Info
                  </Typography>
                  <Typography variant="body2">
                    Has Public User: {debugResults.debug_info.has_public_user ? 'Yes' : 'No'}
                  </Typography>
                  <Typography variant="body2">
                    Has Membership: {debugResults.debug_info.has_membership ? 'Yes' : 'No'}
                  </Typography>
                  <Typography variant="body2">
                    Is Owner: {debugResults.debug_info.is_owner ? 'Yes' : 'No'}
                  </Typography>
                  <Typography variant="body2">
                    User Role: {debugResults.debug_info.user_role || 'None'}
                  </Typography>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Raw Debug Data
              </Typography>
              <pre style={{ 
                overflow: 'auto', 
                backgroundColor: '#f5f5f5', 
                padding: '16px',
                borderRadius: '4px',
                fontSize: '12px'
              }}>
                {JSON.stringify(debugResults, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}
      </Paper>
    </Container>
  );
};

export default OrganizationDebug;