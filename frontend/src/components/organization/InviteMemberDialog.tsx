import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';

interface InviteMemberDialogProps {
  open: boolean;
  inviteEmail: string;
  inviteRole: string;
  loading: boolean;
  onClose: () => void;
  onEmailChange: (email: string) => void;
  onRoleChange: (role: string) => void;
  onInvite: () => void;
}

const InviteMemberDialog: React.FC<InviteMemberDialogProps> = ({
  open,
  inviteEmail,
  inviteRole,
  loading,
  onClose,
  onEmailChange,
  onRoleChange,
  onInvite
}) => {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Invite Member</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          label="Email Address"
          type="email"
          fullWidth
          variant="outlined"
          value={inviteEmail}
          onChange={(e) => onEmailChange(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && inviteEmail && !loading) {
              onInvite();
            }
          }}
        />
        <FormControl fullWidth margin="dense">
          <InputLabel>Role</InputLabel>
          <Select
            value={inviteRole}
            onChange={(e) => onRoleChange(e.target.value)}
            label="Role"
          >
            <MenuItem value="viewer">Viewer</MenuItem>
            <MenuItem value="member">Member</MenuItem>
            <MenuItem value="admin">Administrator</MenuItem>
          </Select>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onInvite} variant="contained" disabled={!inviteEmail || loading}>
          Invite
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default InviteMemberDialog;