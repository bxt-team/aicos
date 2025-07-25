import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
  Typography,
  CircularProgress
} from '@mui/material';

interface DeleteOrganizationDialogProps {
  open: boolean;
  organizationName: string;
  deleteConfirmation: string;
  loading: boolean;
  error: string;
  onClose: () => void;
  onConfirmationChange: (value: string) => void;
  onDelete: () => void;
}

const DeleteOrganizationDialog: React.FC<DeleteOrganizationDialogProps> = ({
  open,
  organizationName,
  deleteConfirmation,
  loading,
  error,
  onClose,
  onConfirmationChange,
  onDelete
}) => {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle color="error">Delete Organization</DialogTitle>
      <DialogContent>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Warning:</strong> This action cannot be undone. This will permanently delete:
          </Typography>
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            <li>The organization "{organizationName}"</li>
            <li>All projects within this organization</li>
            <li>All content and data associated with these projects</li>
            <li>All member access and permissions</li>
          </ul>
        </Alert>
        
        <Typography variant="body2" sx={{ mb: 2 }}>
          Please type <strong>{organizationName}</strong> to confirm:
        </Typography>
        
        <TextField
          fullWidth
          variant="outlined"
          value={deleteConfirmation}
          onChange={(e) => onConfirmationChange(e.target.value)}
          placeholder="Type organization name here"
          error={!!error && deleteConfirmation !== organizationName}
          helperText={error && deleteConfirmation !== organizationName ? error : ''}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          Cancel
        </Button>
        <Button
          onClick={onDelete}
          color="error"
          variant="contained"
          disabled={deleteConfirmation !== organizationName || loading}
        >
          {loading ? <CircularProgress size={24} /> : 'Delete Organization'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteOrganizationDialog;