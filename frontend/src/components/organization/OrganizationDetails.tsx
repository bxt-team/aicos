import React from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  CircularProgress
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon
} from '@mui/icons-material';

interface OrganizationDetailsProps {
  organization: any;
  orgDetails: any;
  setOrgDetails: (details: any) => void;
  isEditingDetails: boolean;
  setIsEditingDetails: (editing: boolean) => void;
  handleSaveDetails: () => Promise<void>;
  loading: boolean;
  orgLoading: boolean;
}

const OrganizationDetails: React.FC<OrganizationDetailsProps> = ({
  organization,
  orgDetails,
  setOrgDetails,
  isEditingDetails,
  setIsEditingDetails,
  handleSaveDetails,
  loading,
  orgLoading
}) => {
  if (loading || orgLoading) {
    return <CircularProgress />;
  }

  if (!orgDetails) {
    return null;
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Organization Details</Typography>
        {!isEditingDetails ? (
          <IconButton onClick={() => setIsEditingDetails(true)}>
            <EditIcon />
          </IconButton>
        ) : (
          <Button
            startIcon={<SaveIcon />}
            variant="contained"
            onClick={handleSaveDetails}
            disabled={loading}
          >
            Save
          </Button>
        )}
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        <Box sx={{ flex: '1 1 100%' }}>
          <TextField
            fullWidth
            label="Organization ID"
            value={organization.id}
            disabled
            InputProps={{
              readOnly: true,
              sx: { fontFamily: 'monospace' }
            }}
            helperText="This is your organization's unique identifier"
          />
        </Box>
        <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' } }}>
          <TextField
            fullWidth
            label="Name"
            value={orgDetails.name || ''}
            onChange={(e) => setOrgDetails({ ...orgDetails, name: e.target.value })}
            disabled={!isEditingDetails}
          />
        </Box>
        <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' } }}>
          <TextField
            fullWidth
            label="Website"
            value={orgDetails.website || ''}
            onChange={(e) => setOrgDetails({ ...orgDetails, website: e.target.value })}
            disabled={!isEditingDetails}
          />
        </Box>
        <Box sx={{ flex: '1 1 100%' }}>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Beschreibung"
            value={orgDetails.description || ''}
            onChange={(e) => setOrgDetails({ ...orgDetails, description: e.target.value })}
            disabled={!isEditingDetails}
          />
        </Box>
        <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' } }}>
          <TextField
            fullWidth
            label="Abonnement"
            value={orgDetails.subscription_tier || 'free'}
            disabled
          />
        </Box>
        <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' } }}>
          <TextField
            fullWidth
            label="Erstellt am"
            value={new Date(orgDetails.created_at).toLocaleDateString('de-DE')}
            disabled
          />
        </Box>
      </Box>
    </Box>
  );
};

export default OrganizationDetails;