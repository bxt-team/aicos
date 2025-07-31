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
  Link,
  Card,
  CardContent
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
  AutoFixHigh as AutoFixHighIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Visibility as VisibilityIcon
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
  const [enhancedData, setEnhancedData] = useState<any>(null);
  const [showEnhancedView, setShowEnhancedView] = useState(false);
  
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
      
      // Check if project has enhanced data stored
      if (response.data.project.enhanced_data) {
        setEnhancedData(response.data.project.enhanced_data);
        setShowEnhancedView(true);
      }
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
      const updateData: any = {
        name: project.name,
        description: project.description,
        settings: project.settings
      };
      
      // Include enhanced data if available
      if (enhancedData) {
        updateData.enhanced_data = enhancedData;
      }
      
      await apiService.projects.update(project.id, updateData);
      
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
        // Store the full enhanced data
        const aiData = response.data.data;
        setEnhancedData(aiData);
        
        // Update the description with the detailed_description from AI
        const enhancedDescription = aiData.detailed_description || aiData.executive_summary || project.description;
        setProject({ ...project, description: enhancedDescription });
        
        // Show the enhanced view
        setShowEnhancedView(true);
        setSuccess('Project enhanced with AI-generated objectives, milestones, and KPIs');
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
                    <Box sx={{ position: 'absolute', right: 8, top: 8, display: 'flex', gap: 1 }}>
                      <IconButton
                        onClick={handleAIRewrite}
                        disabled={isRewritingDescription}
                        sx={{
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
                      {enhancedData && (
                        <IconButton
                          onClick={() => setShowEnhancedView(!showEnhancedView)}
                          sx={{
                            backgroundColor: 'background.paper',
                            '&:hover': {
                              backgroundColor: 'action.hover',
                            },
                          }}
                          title={showEnhancedView ? 'Hide AI enhancements' : 'Show AI enhancements'}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      )}
                    </Box>
                  )}
                </Box>
              </Grid>
              
              {/* Display enhanced AI data if available */}
              {showEnhancedView && enhancedData && (
                <>
                  <Grid size={12}>
                    <Alert severity="success" sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        AI-Enhanced Project Plan
                      </Typography>
                      <Typography variant="body2">
                        The AI has generated objectives, key results, milestones, and risk analysis for your project.
                      </Typography>
                    </Alert>
                  </Grid>
                  
                  {/* Executive Summary */}
                  {enhancedData.executive_summary && (
                    <Grid size={12}>
                      <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: 'background.default' }}>
                        <Typography variant="h6" gutterBottom>
                          Executive Summary
                        </Typography>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {enhancedData.executive_summary}
                        </Typography>
                      </Paper>
                    </Grid>
                  )}
                  
                  {/* Objectives */}
                  {enhancedData.objectives && enhancedData.objectives.length > 0 && (
                    <Grid size={12}>
                      <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: 'background.default' }}>
                        <Typography variant="h6" gutterBottom>
                          Project Objectives
                        </Typography>
                        <List dense>
                          {enhancedData.objectives.map((objective: string, index: number) => (
                            <ListItem key={index}>
                              <ListItemAvatar>
                                <Avatar sx={{ width: 24, height: 24, bgcolor: 'primary.main' }}>
                                  {index + 1}
                                </Avatar>
                              </ListItemAvatar>
                              <ListItemText primary={objective} />
                            </ListItem>
                          ))}
                        </List>
                      </Paper>
                    </Grid>
                  )}
                  
                  {/* Key Results */}
                  {enhancedData.key_results && enhancedData.key_results.length > 0 && (
                    <Grid size={12}>
                      <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: 'background.default' }}>
                        <Typography variant="h6" gutterBottom>
                          Key Results (KPIs)
                        </Typography>
                        <Grid container spacing={2}>
                          {enhancedData.key_results.map((kr: any, index: number) => (
                            <Grid size={{ xs: 12, md: 6 }} key={index}>
                              <Card variant="outlined">
                                <CardContent>
                                  <Typography variant="subtitle2" color="primary" gutterBottom>
                                    {kr.metric}
                                  </Typography>
                                  <Typography variant="body2" paragraph>
                                    <strong>Target:</strong> {kr.target}
                                  </Typography>
                                  <Typography variant="body2" paragraph>
                                    <strong>Timeframe:</strong> {kr.timeframe}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    <strong>Measurement:</strong> {kr.measurement_method}
                                  </Typography>
                                </CardContent>
                              </Card>
                            </Grid>
                          ))}
                        </Grid>
                      </Paper>
                    </Grid>
                  )}
                  
                  {/* Milestones */}
                  {enhancedData.milestones && enhancedData.milestones.length > 0 && (
                    <Grid size={12}>
                      <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: 'background.default' }}>
                        <Typography variant="h6" gutterBottom>
                          Project Milestones
                        </Typography>
                        <Grid container spacing={2}>
                          {enhancedData.milestones.map((milestone: any, index: number) => (
                            <Grid size={{ xs: 12, md: 6 }} key={index}>
                              <Card variant="outlined">
                                <CardContent>
                                  <Typography variant="subtitle2" color="primary" gutterBottom>
                                    {milestone.name}
                                  </Typography>
                                  <Typography variant="body2" paragraph>
                                    {milestone.description}
                                  </Typography>
                                  <Typography variant="caption" display="block" gutterBottom>
                                    <strong>Due:</strong> {milestone.estimated_completion}
                                  </Typography>
                                  {milestone.deliverables && milestone.deliverables.length > 0 && (
                                    <>
                                      <Typography variant="caption" color="text.secondary">
                                        <strong>Deliverables:</strong>
                                      </Typography>
                                      <List dense sx={{ mt: 0.5 }}>
                                        {milestone.deliverables.map((deliverable: string, idx: number) => (
                                          <ListItem key={idx} sx={{ py: 0 }}>
                                            <ListItemText 
                                              primary={deliverable} 
                                              primaryTypographyProps={{ variant: 'caption' }}
                                            />
                                          </ListItem>
                                        ))}
                                      </List>
                                    </>
                                  )}
                                </CardContent>
                              </Card>
                            </Grid>
                          ))}
                        </Grid>
                      </Paper>
                    </Grid>
                  )}
                  
                  {/* Success Factors */}
                  {enhancedData.success_factors && enhancedData.success_factors.length > 0 && (
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: 'background.default' }}>
                        <Typography variant="h6" gutterBottom>
                          Success Factors
                        </Typography>
                        <List dense>
                          {enhancedData.success_factors.map((factor: string, index: number) => (
                            <ListItem key={index}>
                              <ListItemAvatar>
                                <Avatar sx={{ width: 24, height: 24, bgcolor: 'success.main' }}>
                                  <CheckCircleIcon sx={{ fontSize: 16 }} />
                                </Avatar>
                              </ListItemAvatar>
                              <ListItemText primary={factor} />
                            </ListItem>
                          ))}
                        </List>
                      </Paper>
                    </Grid>
                  )}
                  
                  {/* Risks and Mitigations */}
                  {enhancedData.risks_and_mitigations && Object.keys(enhancedData.risks_and_mitigations).length > 0 && (
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: 'background.default' }}>
                        <Typography variant="h6" gutterBottom>
                          Risks & Mitigations
                        </Typography>
                        <List dense>
                          {Object.entries(enhancedData.risks_and_mitigations).map(([risk, mitigation], index) => (
                            <ListItem key={index} alignItems="flex-start">
                              <ListItemAvatar>
                                <Avatar sx={{ width: 24, height: 24, bgcolor: 'warning.main' }}>
                                  <WarningIcon sx={{ fontSize: 16 }} />
                                </Avatar>
                              </ListItemAvatar>
                              <ListItemText 
                                primary={<Typography variant="body2" color="error">{risk}</Typography>}
                                secondary={<Typography variant="caption">{String(mitigation)}</Typography>}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Paper>
                    </Grid>
                  )}
                </>
              )}
              
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