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
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  ListItemAvatar,
  Avatar
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  PersonAdd as PersonAddIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Folder as FolderIcon,
  Person as PersonIcon,
  Group as GroupIcon
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
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
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ProjectManagement: React.FC = () => {
  const { } = useSupabaseAuth();
  // TODO: Add organization support later
  const currentOrganization: any = null;
  const currentProject: any = null;
  const setCurrentProject = (project: any) => {};
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Projects list
  const [projects, setProjects] = useState<any[]>([]);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  
  // Project details
  const [projectDetails, setProjectDetails] = useState<any>(null);
  const [isEditingDetails, setIsEditingDetails] = useState(false);
  
  // Members
  const [projectMembers, setProjectMembers] = useState<any[]>([]);
  const [addMemberDialogOpen, setAddMemberDialogOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedRole, setSelectedRole] = useState('member');
  const [organizationMembers, setOrganizationMembers] = useState<any[]>([]);

  useEffect(() => {
    if (currentOrganization) {
      loadProjects();
      if (tabValue === 2) {
        loadOrganizationMembers();
      }
    }
  }, [currentOrganization]);

  useEffect(() => {
    if (currentProject && tabValue > 0) {
      loadProjectData();
    }
  }, [currentProject, tabValue]);

  const loadProjects = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await apiService.projects.list(currentOrganization.id);
      setProjects(response.data.projects || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Laden der Projekte');
    } finally {
      setLoading(false);
    }
  };

  const loadProjectData = async () => {
    if (!currentProject) return;
    
    setLoading(true);
    setError('');
    
    try {
      switch (tabValue) {
        case 1: // Details
          const detailsResponse = await apiService.projects.get(currentProject.id);
          setProjectDetails(detailsResponse.data.project);
          break;
        case 2: // Members
          const membersResponse = await apiService.projects.getMembers(currentProject.id);
          setProjectMembers(membersResponse.data.members);
          break;
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Laden der Daten');
    } finally {
      setLoading(false);
    }
  };

  const loadOrganizationMembers = async () => {
    if (!currentOrganization) return;
    
    try {
      const response = await apiService.organizations.getMembers(currentOrganization.id);
      setOrganizationMembers(response.data.members);
    } catch (err: any) {
      console.error('Error loading organization members:', err);
    }
  };

  const handleCreateProject = async () => {
    if (!currentOrganization || !newProjectName.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await apiService.projects.create({
        name: newProjectName,
        description: newProjectDescription,
        organization_id: currentOrganization.id
      });
      
      setSuccess('Projekt erfolgreich erstellt');
      setCreateDialogOpen(false);
      setNewProjectName('');
      setNewProjectDescription('');
      loadProjects();
      
      // Set as current project
      setCurrentProject(response.data.project);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Erstellen des Projekts');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProject = (project: any) => {
    setCurrentProject(project);
    localStorage.setItem('currentProjectId', project.id);
    setSuccess(`Projekt "${project.name}" ausgewählt`);
  };

  const handleSaveDetails = async () => {
    if (!currentProject || !projectDetails) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiService.projects.update(currentProject.id, {
        name: projectDetails.name,
        description: projectDetails.description,
        settings: projectDetails.settings
      });
      
      setSuccess('Projekt erfolgreich aktualisiert');
      setIsEditingDetails(false);
      
      // Update current project in context
      setCurrentProject({ ...currentProject, name: projectDetails.name });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Speichern');
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async () => {
    if (!currentProject || !selectedUserId) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiService.projects.addMember(currentProject.id, {
        user_id: selectedUserId,
        role: selectedRole
      });
      
      setSuccess('Mitglied erfolgreich hinzugefügt');
      setAddMemberDialogOpen(false);
      setSelectedUserId('');
      setSelectedRole('member');
      loadProjectData(); // Reload members
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Hinzufügen des Mitglieds');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!currentProject) return;
    
    if (!window.confirm('Möchten Sie dieses Mitglied wirklich aus dem Projekt entfernen?')) return;
    
    try {
      // Note: This endpoint might need to be added to the backend
      await apiService.projects.delete(`${currentProject.id}/members/${memberId}`);
      setSuccess('Mitglied erfolgreich entfernt');
      loadProjectData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Entfernen');
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!window.confirm('Möchten Sie dieses Projekt wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.')) return;
    
    try {
      await apiService.projects.delete(projectId);
      setSuccess('Projekt erfolgreich gelöscht');
      
      // If deleted project was current, clear selection
      if (currentProject?.id === projectId) {
        setCurrentProject(null);
        localStorage.removeItem('currentProjectId');
      }
      
      loadProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen des Projekts');
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

  const getAvailableMembers = () => {
    // Filter out members who are already in the project
    const projectMemberIds = projectMembers.map(m => m.id);
    return organizationMembers.filter(m => !projectMemberIds.includes(m.id));
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
            <Tab label="Projekte" icon={<FolderIcon />} iconPosition="start" />
            <Tab 
              label="Details" 
              icon={<EditIcon />} 
              iconPosition="start"
              disabled={!currentProject}
            />
            <Tab 
              label="Mitglieder" 
              icon={<GroupIcon />} 
              iconPosition="start"
              disabled={!currentProject}
            />
          </Tabs>
        </Box>

        {error && <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ m: 2 }}>{success}</Alert>}

        <TabPanel value={tabValue} index={0}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h5">Projekte in {currentOrganization.name}</Typography>
              <Button
                startIcon={<AddIcon />}
                variant="contained"
                onClick={() => setCreateDialogOpen(true)}
              >
                Neues Projekt
              </Button>
            </Box>

            {loading ? (
              <CircularProgress />
            ) : projects.length === 0 ? (
              <Alert severity="info">
                Noch keine Projekte vorhanden. Erstellen Sie Ihr erstes Projekt!
              </Alert>
            ) : (
              <Grid container spacing={3}>
                {projects.map((project) => (
                  <Grid size={{ xs: 12, md: 6, lg: 4 }} key={project.id}>
                    <Card 
                      sx={{ 
                        cursor: 'pointer',
                        border: currentProject?.id === project.id ? 2 : 0,
                        borderColor: 'primary.main'
                      }}
                      onClick={() => handleSelectProject(project)}
                    >
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="start">
                          <Box>
                            <Typography variant="h6" gutterBottom>
                              {project.name}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" paragraph>
                              {project.description || 'Keine Beschreibung'}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              Erstellt: {new Date(project.created_at).toLocaleDateString('de-DE')}
                            </Typography>
                          </Box>
                          {project.role === 'owner' && (
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteProject(project.id);
                              }}
                            >
                              <DeleteIcon />
                            </IconButton>
                          )}
                        </Box>
                        {currentProject?.id === project.id && (
                          <Chip
                            label="Aktiv"
                            color="primary"
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {loading ? (
            <CircularProgress />
          ) : projectDetails ? (
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h5">Projektdetails</Typography>
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
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Name"
                    value={projectDetails.name || ''}
                    onChange={(e) => setProjectDetails({ ...projectDetails, name: e.target.value })}
                    disabled={!isEditingDetails}
                  />
                </Grid>
                <Grid size={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Beschreibung"
                    value={projectDetails.description || ''}
                    onChange={(e) => setProjectDetails({ ...projectDetails, description: e.target.value })}
                    disabled={!isEditingDetails}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Erstellt am"
                    value={new Date(projectDetails.created_at).toLocaleDateString('de-DE')}
                    disabled
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Ihre Rolle"
                    value={projectDetails.role || 'member'}
                    disabled
                  />
                </Grid>
              </Grid>
            </Box>
          ) : null}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h5">Projektmitglieder</Typography>
              <Button
                startIcon={<PersonAddIcon />}
                variant="contained"
                onClick={() => {
                  loadOrganizationMembers();
                  setAddMemberDialogOpen(true);
                }}
              >
                Mitglied hinzufügen
              </Button>
            </Box>

            {loading ? (
              <CircularProgress />
            ) : (
              <List>
                {projectMembers.map((member) => (
                  <ListItem key={member.id}>
                    <ListItemAvatar>
                      <Avatar>
                        <PersonIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={member.name}
                      secondary={
                        <React.Fragment>
                          {member.email}
                          <Chip
                            label={member.role}
                            color={getRoleColor(member.role)}
                            size="small"
                            sx={{ ml: 1 }}
                          />
                        </React.Fragment>
                      }
                    />
                    {member.role !== 'owner' && currentProject?.role === 'owner' && (
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          onClick={() => handleRemoveMember(member.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    )}
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </TabPanel>
      </Paper>

      {/* Create Project Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Neues Projekt erstellen</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Projektname"
            fullWidth
            variant="outlined"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
          />
          <TextField
            margin="dense"
            label="Beschreibung (optional)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newProjectDescription}
            onChange={(e) => setNewProjectDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Abbrechen</Button>
          <Button 
            onClick={handleCreateProject} 
            variant="contained" 
            disabled={!newProjectName.trim() || loading}
          >
            Erstellen
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Member Dialog */}
      <Dialog open={addMemberDialogOpen} onClose={() => setAddMemberDialogOpen(false)}>
        <DialogTitle>Mitglied hinzufügen</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Mitglied auswählen</InputLabel>
            <Select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              label="Mitglied auswählen"
            >
              {getAvailableMembers().map((member) => (
                <MenuItem key={member.id} value={member.id}>
                  {member.name} ({member.email})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Rolle</InputLabel>
            <Select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              label="Rolle"
            >
              <MenuItem value="viewer">Betrachter</MenuItem>
              <MenuItem value="member">Mitglied</MenuItem>
              <MenuItem value="admin">Administrator</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddMemberDialogOpen(false)}>Abbrechen</Button>
          <Button 
            onClick={handleAddMember} 
            variant="contained" 
            disabled={!selectedUserId || loading}
          >
            Hinzufügen
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProjectManagement;