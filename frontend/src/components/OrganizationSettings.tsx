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
  Grid,
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
    updateMemberRole
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
      setError(err.response?.data?.detail || 'Fehler beim Laden der Daten');
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
      
      setSuccess('Organisation erfolgreich aktualisiert');
      setIsEditingDetails(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern');
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
      
      setSuccess('Einladung erfolgreich versendet');
      setInviteDialogOpen(false);
      setInviteEmail('');
      setInviteRole('member');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Einladen');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateMemberRole = async (memberId: string, newRole: string) => {
    setError('');
    setSuccess('');
    
    try {
      await updateMemberRole(memberId, newRole);
      setSuccess('Rolle erfolgreich aktualisiert');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Aktualisieren der Rolle');
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!window.confirm('Möchten Sie dieses Mitglied wirklich entfernen?')) return;
    
    setError('');
    setSuccess('');
    
    try {
      await removeMember(memberId);
      setSuccess('Mitglied erfolgreich entfernt');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Entfernen');
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

  if (!currentOrganization) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="info">Bitte wählen Sie eine Organisation aus</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Paper elevation={3}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Allgemein" />
            <Tab label="Mitglieder" />
            <Tab label="Nutzung" />
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
                <Typography variant="h5">Organisationsdetails</Typography>
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
                    Speichern
                  </Button>
                )}
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Name"
                    value={orgDetails.name || ''}
                    onChange={(e) => setOrgDetails({ ...orgDetails, name: e.target.value })}
                    disabled={!isEditingDetails}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Website"
                    value={orgDetails.website || ''}
                    onChange={(e) => setOrgDetails({ ...orgDetails, website: e.target.value })}
                    disabled={!isEditingDetails}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Beschreibung"
                    value={orgDetails.description || ''}
                    onChange={(e) => setOrgDetails({ ...orgDetails, description: e.target.value })}
                    disabled={!isEditingDetails}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Abonnement"
                    value={orgDetails.subscription_tier || 'free'}
                    disabled
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Erstellt am"
                    value={new Date(orgDetails.created_at).toLocaleDateString('de-DE')}
                    disabled
                  />
                </Grid>
              </Grid>
            </Box>
          ) : null}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h5">Mitglieder</Typography>
              <Button
                startIcon={<PersonAddIcon />}
                variant="contained"
                onClick={() => setInviteDialogOpen(true)}
              >
                Mitglied einladen
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
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6} lg={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Projekte
                      </Typography>
                      <Typography variant="h4">
                        {usage.projects.current}/{usage.projects.limit}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={6} lg={3}>
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
                </Grid>
                
                <Grid item xs={12} md={6} lg={3}>
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
                </Grid>
                
                <Grid item xs={12} md={6} lg={3}>
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
                </Grid>
              </Grid>
            </Box>
          ) : null}
        </TabPanel>
      </Paper>

      {/* Invite Member Dialog */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)}>
        <DialogTitle>Mitglied einladen</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="E-Mail Adresse"
            type="email"
            fullWidth
            variant="outlined"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel>Rolle</InputLabel>
            <Select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              label="Rolle"
            >
              <MenuItem value="viewer">Betrachter</MenuItem>
              <MenuItem value="member">Mitglied</MenuItem>
              <MenuItem value="admin">Administrator</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)}>Abbrechen</Button>
          <Button onClick={handleInviteMember} variant="contained" disabled={!inviteEmail || loading}>
            Einladen
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default OrganizationSettings;