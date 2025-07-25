import React from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  Card,
  CardContent
} from '@mui/material';

interface OrganizationDangerZoneProps {
  isOwner: boolean;
  loading: boolean;
  onDeleteOrganization: () => void;
}

const OrganizationDangerZone: React.FC<OrganizationDangerZoneProps> = ({
  isOwner,
  loading,
  onDeleteOrganization
}) => {
  return (
    <Box>
      <Alert severity="warning" sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>Danger Zone</Typography>
        <Typography variant="body2">
          The following actions are irreversible. Please proceed with caution.
        </Typography>
      </Alert>

      <Card sx={{ border: 1, borderColor: 'error.main', bgcolor: 'error.50' }}>
        <CardContent>
          <Typography variant="h6" color="error" gutterBottom>
            Delete Organization
          </Typography>
          <Typography variant="body2" paragraph>
            Once you delete an organization, there is no going back. All data including projects, 
            content, and settings will be permanently deleted.
          </Typography>
          
          {/* Only show delete button if user is owner */}
          {isOwner ? (
            <Button
              variant="contained"
              color="error"
              onClick={onDeleteOrganization}
              disabled={loading}
            >
              Delete This Organization
            </Button>
          ) : (
            <Alert severity="info">
              Only organization owners can delete the organization.
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default OrganizationDangerZone;