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
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  Avatar,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Breadcrumbs,
  Link
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  PersonAdd as PersonAddIcon,
  Person as PersonIcon,
  Delete as DeleteIcon,
  Description as DescriptionIcon,
  Group as GroupIcon,
  ArrowBack as ArrowBackIcon,
  AutoFixHigh as AutoFixHighIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { useProject } from '../contexts/ProjectContext';
import { apiService } from '../services/api';
import { useTranslation } from 'react-i18next';

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
      id={`project-detail-tabpanel-${index}`}
      aria-labelledby={`project-detail-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ProjectDetail: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const { user } = useSupabaseAuth();
  const { currentOrganization } = useOrganization();
  const { updateProject: updateProjectInContext } = useProject();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Project details
  const [project, setProject] = useState<any>(null);
  const [isEditingDetails, setIsEditingDetails] = useState(false);
  const [isRewritingDescription, setIsRewritingDescription] = useState(false);
  
  // Members
  const [projectMembers, setProjectMembers] = useState<any[]>([]);
  const [addMemberDialogOpen, setAddMemberDialogOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedRole, setSelectedRole] = useState('member');
  const [organizationMembers, setOrganizationMembers] = useState<any[]>([]);


  useEffect(() => {
    if (projectId && currentOrganization) {
      loadProject();
    }
  }, [projectId, currentOrganization]);

  useEffect(() => {
    if (project && tabValue > 0) {
      loadProjectData();
    }
  }, [project, tabValue]);

  const loadProject = async () => {
    if (!projectId) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await apiService.projects.get(projectId);
      setProject(response.data.project);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.errorLoading', { resource: t('project.project').toLowerCase() }));
    } finally {
      setLoading(false);
    }
  };

  const loadProjectData = async () => {
    if (!project) return;
    
    setLoading(true);
    setError('');
    
    try {
      switch (tabValue) {
        case 0: // Details - already loaded
          break;
        case 1: // Members
          const membersResponse = await apiService.projects.getMembers(project.id);
          setProjectMembers(membersResponse.data.members || []);
          break;
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.errorLoading', { resource: t('common.data', 'data') }));
    } finally {
      setLoading(false);
    }
  };

  const loadOrganizationMembers = async () => {
    if (!currentOrganization) return;
    
    try {
      const response = await apiService.organizations.getMembers(currentOrganization.id);
      setOrganizationMembers(response.data.members || []);
    } catch (err: any) {
      console.error('Error loading organization members:', err);
    }
  };

  const handleSaveDetails = async () => {
    if (!project) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiService.projects.update(project.id, {
        name: project.name,
        description: project.description,
        settings: project.settings
      });
      
      // Update project in context to refresh sidebar
      await updateProjectInContext(project.id, {
        name: project.name,
        description: project.description
      });
      
      setSuccess('Project successfully updated');
      setIsEditingDetails(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.errorSaving'));
    } finally {
      setLoading(false);
    }
  };

  const handleAIRewrite = async () => {
    if (!project || !currentOrganization) return;
    
    setIsRewritingDescription(true);
    setError('');
    
    try {
      const response = await apiService.organizationManagement.enhanceProjectDescription({
        raw_description: project.description || '',
        organization_purpose: currentOrganization.description || '',
        organization_goals: [], // Organizations don't have goals stored yet
        department: project.department || undefined,
        user_feedback: undefined,
        previous_result: undefined
      });
      
      if (response.data.success && response.data.data) {
        // Extract the enhanced description from the AI response
        const enhancedData = response.data.data;
        let enhancedDescription = project.description || '';
        
        if (enhancedData.description) {
          enhancedDescription = enhancedData.description;
        } else if (enhancedData.enhanced_description) {
          enhancedDescription = enhancedData.enhanced_description;
        } else if (typeof enhancedData === 'string') {
          enhancedDescription = enhancedData;
        }
        
        setProject({ ...project, description: enhancedDescription });
        setSuccess('Description enhanced with AI');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to enhance description with AI');
    } finally {
      setIsRewritingDescription(false);
    }
  };

  const handleAddMember = async () => {
    if (!project || !selectedUserId) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiService.projects.addMember(project.id, {
        user_id: selectedUserId,
        role: selectedRole
      });
      
      setSuccess('Member added successfully');
      setAddMemberDialogOpen(false);
      setSelectedUserId('');
      setSelectedRole('member');
      loadProjectData(); // Reload members
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToCreate', { resource: t('organization.member').toLowerCase() }));
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!project) return;
    
    if (!window.confirm('Are you sure you want to remove this member from the project?')) return;
    
    try {
      await apiService.projects.delete(`${project.id}/members/${memberId}`);
      setSuccess('Member removed successfully');
      loadProjectData();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToDelete', { resource: t('organization.member').toLowerCase() }));
    }
  };

  const handleUpdateMemberRole = async (memberId: string, newRole: string) => {
    if (!project) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiService.projects.updateMemberRole(project.id, memberId, newRole);
      setSuccess('Member role updated successfully');
      loadProjectData();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToUpdate', { resource: t('project.memberRole', 'member role') }));
    } finally {
      setLoading(false);
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
    const projectMemberIds = projectMembers.map(m => m.id);
    return organizationMembers.filter(m => !projectMemberIds.includes(m.id));
  };

  if (loading && !project) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!project) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Project not found</Alert>
      </Container>
    );
  }

  const currentUserRole = project.role || projectMembers.find(m => m.user_id === user?.id)?.role;
  const isAdmin = currentUserRole === 'owner' || currentUserRole === 'admin';

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box mb={3}>
        <Breadcrumbs aria-label="breadcrumb">
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/organization-settings/projects')}
            sx={{ textDecoration: 'none', cursor: 'pointer' }}
          >
            {currentOrganization?.name}
          </Link>
          <Typography color="text.primary">{project.name}</Typography>
        </Breadcrumbs>
      </Box>

      <Paper elevation={3}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', px: 2, pt: 2 }}>
            <IconButton onClick={() => navigate('/organization-settings/projects')} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h5" sx={{ flexGrow: 1 }}>
              {project.name}
            </Typography>
          </Box>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ px: 2 }}>
            <Tab label={t('common.details')} icon={<DescriptionIcon />} iconPosition="start" />
            <Tab label={t('organization.members')} icon={<GroupIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        {error && <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ m: 2 }}>{success}</Alert>}

        <TabPanel value={tabValue} index={0}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h6">{t('project.projectDetails')}</Typography>
              {isAdmin && (
                !isEditingDetails ? (
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
                )
              )}
            </Box>

            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label={t('common.name')}
                  value={project.name || ''}
                  onChange={(e) => setProject({ ...project, name: e.target.value })}
                  disabled={!isEditingDetails}
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <Box sx={{ position: 'relative' }}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label={t('project.goalsAndDescription', 'Goals & Description')}
                    value={project.description || ''}
                    onChange={(e) => setProject({ ...project, description: e.target.value })}
                    disabled={!isEditingDetails || isRewritingDescription}
                    sx={{ pr: isEditingDetails ? 6 : 0 }}
                  />
                  {isEditingDetails && (
                    <IconButton
                      onClick={handleAIRewrite}
                      disabled={isRewritingDescription}
                      sx={{
                        position: 'absolute',
                        right: 8,
                        top: 8,
                        backgroundColor: 'background.paper',
                        '&:hover': {
                          backgroundColor: 'action.hover',
                        },
                      }}
                      title={t('project.aiRewrite', 'AI Rewrite')}
                    >
                      {isRewritingDescription ? (
                        <CircularProgress size={20} />
                      ) : (
                        <AutoFixHighIcon />
                      )}
                    </IconButton>
                  )}
                </Box>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label={t('project.createdAt')}
                  value={new Date(project.created_at).toLocaleDateString()}
                  disabled
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label={t('project.yourRole', 'Your Role')}
                  value={currentUserRole || 'member'}
                  disabled
                />
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h6">{t('project.projectMembers', 'Project Members')}</Typography>
              {isAdmin && (
                <Button
                  startIcon={<PersonAddIcon />}
                  variant="contained"
                  onClick={() => {
                    loadOrganizationMembers();
                    setAddMemberDialogOpen(true);
                  }}
                >
                  Add Member
                </Button>
              )}
            </Box>

            {loading ? (
              <CircularProgress />
            ) : projectMembers.length === 0 ? (
              <Typography color="text.secondary" sx={{ py: 2 }}>
                No members found. Add members to collaborate on this project.
              </Typography>
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
                      primary={member.name || member.email}
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
                    {member.role !== 'owner' && isAdmin && (
                      <ListItemSecondaryAction>
                        <FormControl size="small" sx={{ mr: 1, minWidth: 100 }}>
                          <Select
                            value={member.role}
                            onChange={(e) => handleUpdateMemberRole(member.id, e.target.value)}
                            disabled={loading}
                          >
                            <MenuItem value="viewer">Viewer</MenuItem>
                            <MenuItem value="member">Member</MenuItem>
                            <MenuItem value="admin">Admin</MenuItem>
                          </Select>
                        </FormControl>
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

      {/* Add Member Dialog */}
      <Dialog open={addMemberDialogOpen} onClose={() => setAddMemberDialogOpen(false)}>
        <DialogTitle>Add Member</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Select Member</InputLabel>
            <Select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              label={t('task.selectMember')}
            >
              {getAvailableMembers().map((member) => (
                <MenuItem key={member.id} value={member.id}>
                  {member.name || member.email} ({member.email})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Role</InputLabel>
            <Select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              label={t('organization.role')}
            >
              <MenuItem value="viewer">Viewer</MenuItem>
              <MenuItem value="member">Member</MenuItem>
              <MenuItem value="admin">Administrator</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddMemberDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleAddMember} 
            variant="contained" 
            disabled={!selectedUserId || loading}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProjectDetail;