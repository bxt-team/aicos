import React from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Select,
  MenuItem,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  Delete as DeleteIcon,
  PersonAdd as PersonAddIcon
} from '@mui/icons-material';

interface OrganizationMembersProps {
  members: any[];
  loading: boolean;
  currentUserRole?: string;
  onInviteMember: () => void;
  onUpdateMemberRole: (memberId: string, newRole: string) => Promise<void>;
  onRemoveMember: (memberId: string) => Promise<void>;
  getRoleColor: (role: string) => "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning";
}

const OrganizationMembers: React.FC<OrganizationMembersProps> = ({
  members,
  loading,
  currentUserRole,
  onInviteMember,
  onUpdateMemberRole,
  onRemoveMember,
  getRoleColor
}) => {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Members</Typography>
        <Button
          startIcon={<PersonAddIcon />}
          variant="contained"
          onClick={onInviteMember}
        >
          Invite Member
        </Button>
      </Box>

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>E-Mail</TableCell>
                <TableCell>Rolle</TableCell>
                <TableCell>Beigetreten</TableCell>
                <TableCell align="right">Aktionen</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {members.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography color="textSecondary">
                      No members found. If this is unexpected, check the browser console for errors.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                members.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>{member.name || member.email.split('@')[0]}</TableCell>
                    <TableCell>{member.email}</TableCell>
                    <TableCell>
                      {/* Allow role change for non-owners and non-current user */}
                      {!member.is_current_user && members.find(m => m.is_current_user)?.role === 'owner' ? (
                        <Select
                          value={member.role}
                          onChange={(e) => onUpdateMemberRole(member.id, e.target.value)}
                          size="small"
                          disabled={loading}
                        >
                          <MenuItem value="viewer">Viewer</MenuItem>
                          <MenuItem value="member">Member</MenuItem>
                          <MenuItem value="admin">Admin</MenuItem>
                          <MenuItem value="owner">Owner</MenuItem>
                        </Select>
                      ) : (
                        <Chip
                          label={member.role}
                          color={getRoleColor(member.role)}
                          size="small"
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      {new Date(member.joined_at).toLocaleDateString('de-DE')}
                    </TableCell>
                    <TableCell align="right">
                      {member.role !== 'owner' && !member.is_current_user && (
                        <IconButton
                          size="small"
                          onClick={() => onRemoveMember(member.id)}
                          disabled={loading}
                        >
                          <DeleteIcon />
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default OrganizationMembers;