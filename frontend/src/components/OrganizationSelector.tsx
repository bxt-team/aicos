import React, { useState } from 'react';
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  IconButton,
  Divider,
  Stack,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  Business as BusinessIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useOrganization } from '../contexts/OrganizationContext';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useNavigate } from 'react-router-dom';

const OrganizationSelector: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSupabaseAuth();
  const {
    organizations,
    currentOrganization,
    setCurrentOrganization,
    createOrganization,
    loading,
    error
  } = useOrganization();

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgDescription, setNewOrgDescription] = useState('');
  const [createError, setCreateError] = useState('');
  const [creating, setCreating] = useState(false);

  const handleOrganizationChange = (orgId: string) => {
    const org = organizations.find(o => o.id === orgId);
    if (org) {
      setCurrentOrganization(org);
    }
  };

  const handleCreateOrganization = async () => {
    if (!newOrgName.trim()) {
      setCreateError('Organization name is required');
      return;
    }

    setCreating(true);
    setCreateError('');

    try {
      await createOrganization({
        name: newOrgName.trim(),
        description: newOrgDescription.trim() || undefined
      });

      // Reset form and close dialog
      setNewOrgName('');
      setNewOrgDescription('');
      setCreateDialogOpen(false);
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Failed to create organization');
    } finally {
      setCreating(false);
    }
  };

  const handleOpenSettings = () => {
    navigate('/organization-settings');
  };

  if (!user) {
    return null;
  }

  if (loading && organizations.length === 0) {
    return (
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={20} />
        <Typography variant="body2" color="text.secondary">
          Loading organizations...
        </Typography>
      </Box>
    );
  }

  return (
    <>
      <Box sx={{ p: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Stack spacing={2}>
          <FormControl fullWidth size="small">
            <InputLabel id="org-select-label">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <BusinessIcon fontSize="small" />
                Organization
              </Box>
            </InputLabel>
            <Select
              labelId="org-select-label"
              value={currentOrganization?.id || ''}
              onChange={(e) => handleOrganizationChange(e.target.value)}
              label="Organization"
              sx={{ pr: 1 }}
            >
              {organizations.map((org) => (
                <MenuItem key={org.id} value={org.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                    <Typography>{org.name}</Typography>
                    {org.subscription_tier && (
                      <Chip 
                        label={org.subscription_tier} 
                        size="small" 
                        sx={{ ml: 1 }}
                        color={org.subscription_tier === 'pro' ? 'primary' : 'default'}
                      />
                    )}
                  </Box>
                </MenuItem>
              ))}
              <Divider />
              <MenuItem onClick={() => setCreateDialogOpen(true)}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'primary.main' }}>
                  <AddIcon fontSize="small" />
                  Create New Organization
                </Box>
              </MenuItem>
            </Select>
          </FormControl>

          {currentOrganization && (
            <Button
              size="small"
              startIcon={<SettingsIcon />}
              onClick={handleOpenSettings}
              sx={{ justifyContent: 'flex-start' }}
            >
              Organization Settings
            </Button>
          )}
        </Stack>

        {organizations.length === 0 && !loading && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              No organizations yet
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
              size="small"
              fullWidth
            >
              Create Your First Organization
            </Button>
          </Box>
        )}
      </Box>

      {/* Create Organization Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => !creating && setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Organization</DialogTitle>
        <DialogContent>
          {createError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {createError}
            </Alert>
          )}
          
          <TextField
            autoFocus
            margin="dense"
            label="Organization Name"
            fullWidth
            variant="outlined"
            value={newOrgName}
            onChange={(e) => setNewOrgName(e.target.value)}
            disabled={creating}
            required
            sx={{ mb: 2 }}
          />
          
          <TextField
            margin="dense"
            label="Description (optional)"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={newOrgDescription}
            onChange={(e) => setNewOrgDescription(e.target.value)}
            disabled={creating}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)} disabled={creating}>
            Cancel
          </Button>
          <Button
            onClick={handleCreateOrganization}
            variant="contained"
            disabled={creating || !newOrgName.trim()}
            startIcon={creating && <CircularProgress size={20} />}
          >
            {creating ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default OrganizationSelector;