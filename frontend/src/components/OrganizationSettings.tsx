import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Tabs,
  Tab,
  Box,
  TextField,
  Button,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Card,
  CardContent
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  PersonAdd as PersonAddIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { apiService } from '../services/api';
import { useNavigate } from 'react-router-dom';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`org-tabpanel-${index}`}
      aria-labelledby={`org-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const OrganizationSettings: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSupabaseAuth();
  const {
    currentOrganization,
    members,
    loading: orgLoading,
    error: orgError,
    updateOrganization,
    loadMembers,
    inviteMember,
    removeMember,
    updateMemberRole,
    deleteOrganization
  } = useOrganization();
  
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Organization details
  const [orgDetails, setOrgDetails] = useState<any>(null);
  const [isEditingDetails, setIsEditingDetails] = useState(false);
  
  // Invite dialog
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  
  // Delete organization dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  
  // Usage stats
  const [usage, setUsage] = useState<any>(null);

  useEffect(() => {
    if (currentOrganization) {
      loadOrganizationData();
    }
  }, [currentOrganization, tabValue]);

  useEffect(() => {
    // Initialize org details when currentOrganization changes
    if (currentOrganization) {
      setOrgDetails({
        name: currentOrganization.name,
        description: currentOrganization.description || '',
        website: currentOrganization.website || '',
        subscription_tier: currentOrganization.subscription_tier,
        created_at: currentOrganization.created_at
      });
    }
  }, [currentOrganization]);

  const loadOrganizationData = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    setError('');
    
    try {
      switch (tabValue) {
        case 0: // General - already loaded from context
          break;
        case 1: // Members - loaded from context
          if (members.length === 0) {
            await loadMembers();
          }
          break;
        case 2: // Usage
          const usageResponse = await apiService.organizations.getUsage(currentOrganization.id);
          setUsage(usageResponse.data.usage);
          break;
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading data');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDetails = async () => {
    if (!currentOrganization || !orgDetails) return;
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await updateOrganization(currentOrganization.id, {
        name: orgDetails.name,
        description: orgDetails.description,
        website: orgDetails.website
      });
      
      setSuccess('Organization successfully updated');
      setIsEditingDetails(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error saving');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteMember = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await inviteMember(inviteEmail, inviteRole);
      
      setSuccess('Invitation sent successfully');
      setInviteDialogOpen(false);
      setInviteEmail('');
      setInviteRole('member');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error inviting');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateMemberRole = async (memberId: string, newRole: string) => {
    setError('');
    setSuccess('');
    
    try {
      await updateMemberRole(memberId, newRole);
      setSuccess('Role successfully updated');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error updating role');
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;
    
    setError('');
    setSuccess('');
    
    try {
      await removeMember(memberId);
      setSuccess('Member successfully removed');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error removing member');
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'owner': return 'error';
      case 'admin': return 'warning';
      case 'member': return 'primary';
      case 'viewer': return 'default';
      default: return 'default';
    }
  };
  
  const handleDeleteOrganization = async () => {
    if (!currentOrganization) return;
    
    if (deleteConfirmation !== currentOrganization.name) {
      setError('Please type the organization name correctly to confirm deletion');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await deleteOrganization(currentOrganization.id);
      setSuccess('Organization deleted successfully');
      
      // Redirect to home or organizations list after a short delay
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to delete organization');
      setLoading(false);
    }
  };

  if (!currentOrganization) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="info">Please select an organization</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Paper elevation={3}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Allgemein" />
            <Tab label="Members" />
            <Tab label="Nutzung" />
            <Tab label="Danger Zone" sx={{ color: 'error.main' }} />
          </Tabs>
        </Box>

        {error && <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ m: 2 }}>{success}</Alert>}

        <TabPanel value={tabValue} index={0}>
          {(loading || orgLoading) ? (
            <CircularProgress />
          ) : orgDetails ? (
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
          ) : null}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h5">Members</Typography>
              <Button
                startIcon={<PersonAddIcon />}
                variant="contained"
                onClick={() => setInviteDialogOpen(true)}
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
                    {members.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell>{member.name || member.email.split('@')[0]}</TableCell>
                        <TableCell>{member.email}</TableCell>
                        <TableCell>
                          <Chip
                            label={member.role}
                            color={getRoleColor(member.role)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(member.joined_at).toLocaleDateString('de-DE')}
                        </TableCell>
                        <TableCell align="right">
                          {member.role !== 'owner' && member.user_id !== user?.id && (
                            <IconButton
                              size="small"
                              onClick={() => handleRemoveMember(member.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {loading ? (
            <CircularProgress />
          ) : usage ? (
            <Box>
              <Typography variant="h5" gutterBottom>Nutzungsstatistik</Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' }, '@media (min-width: 1200px)': { flex: '1 1 22%' } }}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Projects
                      </Typography>
                      <Typography variant="h4">
                        {usage.projects.current}/{usage.projects.limit}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
                
                <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' }, '@media (min-width: 1200px)': { flex: '1 1 22%' } }}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Benutzer
                      </Typography>
                      <Typography variant="h4">
                        {usage.users.current}/{usage.users.limit}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
                
                <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' }, '@media (min-width: 1200px)': { flex: '1 1 22%' } }}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Speicher (GB)
                      </Typography>
                      <Typography variant="h4">
                        {usage.storage.current_gb}/{usage.storage.limit_gb}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
                
                <Box sx={{ flex: '1 1 100%', '@media (min-width: 900px)': { flex: '1 1 45%' }, '@media (min-width: 1200px)': { flex: '1 1 22%' } }}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        API-Aufrufe (Monat)
                      </Typography>
                      <Typography variant="h4">
                        {usage.api_calls.current_month.toLocaleString('de-DE')}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
              </Box>
            </Box>
          ) : null}
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
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
                {members.find(m => m.user_id === user?.id)?.role === 'owner' ? (
                  <Button
                    variant="contained"
                    color="error"
                    onClick={() => setDeleteDialogOpen(true)}
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
        </TabPanel>
      </Paper>

      {/* Invite Member Dialog */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)}>
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
            onChange={(e) => setInviteEmail(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && inviteEmail && !loading) {
                handleInviteMember();
              }
            }}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel>Role</InputLabel>
            <Select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              label="Role"
            >
              <MenuItem value="viewer">Viewer</MenuItem>
              <MenuItem value="member">Member</MenuItem>
              <MenuItem value="admin">Administrator</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleInviteMember} variant="contained" disabled={!inviteEmail || loading}>
            Invite
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Organization Dialog */}
      <Dialog 
        open={deleteDialogOpen} 
        onClose={() => {
          setDeleteDialogOpen(false);
          setDeleteConfirmation('');
        }}
      >
        <DialogTitle color="error">Delete Organization</DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Warning:</strong> This action cannot be undone. This will permanently delete:
            </Typography>
            <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
              <li>The organization "{currentOrganization?.name}"</li>
              <li>All projects within this organization</li>
              <li>All content and data associated with these projects</li>
              <li>All member access and permissions</li>
            </ul>
          </Alert>
          
          <Typography variant="body2" sx={{ mb: 2 }}>
            Please type <strong>{currentOrganization?.name}</strong> to confirm:
          </Typography>
          
          <TextField
            fullWidth
            variant="outlined"
            value={deleteConfirmation}
            onChange={(e) => setDeleteConfirmation(e.target.value)}
            placeholder="Type organization name here"
            error={!!error && deleteConfirmation !== currentOrganization?.name}
            helperText={error && deleteConfirmation !== currentOrganization?.name ? error : ''}
          />
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => {
              setDeleteDialogOpen(false);
              setDeleteConfirmation('');
              setError('');
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteOrganization}
            color="error"
            variant="contained"
            disabled={deleteConfirmation !== currentOrganization?.name || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Delete Organization'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default OrganizationSettings;