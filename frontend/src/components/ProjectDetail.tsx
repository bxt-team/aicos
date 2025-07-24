import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Tab,
  Tabs,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Chip,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  ListItemSecondaryAction,
  IconButton,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Divider
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  ArrowBack as ArrowBackIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Person as PersonIcon,
  PersonAdd as PersonAddIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';

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
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useSupabaseAuth();
  const { currentOrganization } = useOrganization();
  
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [activity, setActivity] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Edit mode states
  const [editMode, setEditMode] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [editedDescription, setEditedDescription] = useState('');
  
  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  
  // Member management
  const [addMemberDialogOpen, setAddMemberDialogOpen] = useState(false);
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [newMemberRole, setNewMemberRole] = useState('member');

  useEffect(() => {
    if (projectId) {
      loadProjectData();
    }
  }, [projectId]);

  const loadProjectData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load project details
      const projectResponse = await apiService.projects.get(projectId!);
      const projectData = projectResponse.data;
      setProject(projectData);
      setEditedName(projectData.name);
      setEditedDescription(projectData.description || '');
      
      // Load members
      const membersResponse = await apiService.projects.getMembers(projectId!);
      setMembers(membersResponse.data);
      
      // Load activity and stats based on selected tab
      if (tabValue === 2) {
        const activityResponse = await apiService.projects.getActivity(projectId!);
        setActivity(activityResponse.data);
      } else if (tabValue === 3) {
        const statsResponse = await apiService.projects.getStats(projectId!);
        setStats(statsResponse.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load project data');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveChanges = async () => {
    try {
      await apiService.projects.update(projectId!, {
        name: editedName,
        description: editedDescription
      });
      
      setProject({
        ...project,
        name: editedName,
        description: editedDescription
      });
      
      setEditMode(false);
    } catch (err: any) {
      setError(err.message || 'Failed to update project');
    }
  };

  const handleDeleteProject = async () => {
    if (deleteConfirmation !== project?.name) {
      setError('Please type the project name correctly to confirm deletion');
      return;
    }
    
    try {
      await apiService.projects.delete(projectId!);
      navigate('/projects');
    } catch (err: any) {
      setError(err.message || 'Failed to delete project');
    }
  };

  const handleAddMember = async () => {
    try {
      await apiService.projects.addMember(projectId!, {
        email: newMemberEmail,
        role: newMemberRole
      });
      
      // Reload members
      const membersResponse = await apiService.projects.getMembers(projectId!);
      setMembers(membersResponse.data);
      
      // Reset form
      setAddMemberDialogOpen(false);
      setNewMemberEmail('');
      setNewMemberRole('member');
    } catch (err: any) {
      setError(err.message || 'Failed to add member');
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    try {
      await apiService.projects.removeMember(projectId!, memberId);
      setMembers(members.filter(m => m.id !== memberId));
    } catch (err: any) {
      setError(err.message || 'Failed to remove member');
    }
  };

  const handleUpdateMemberRole = async (memberId: string, newRole: string) => {
    try {
      await apiService.projects.updateMemberRole(projectId!, memberId, newRole);
      setMembers(members.map(m => 
        m.id === memberId ? { ...m, role: newRole } : m
      ));
    } catch (err: any) {
      setError(err.message || 'Failed to update member role');
    }
  };

  const handleTabChange = async (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    
    // Load tab-specific data
    if (newValue === 2 && activity.length === 0) {
      try {
        const activityResponse = await apiService.projects.getActivity(projectId!);
        setActivity(activityResponse.data);
      } catch (err) {
        console.error('Failed to load activity:', err);
      }
    } else if (newValue === 3 && !stats) {
      try {
        const statsResponse = await apiService.projects.getStats(projectId!);
        setStats(statsResponse.data);
      } catch (err) {
        console.error('Failed to load stats:', err);
      }
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!project) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Project not found</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/projects')} sx={{ mt: 2 }}>
          Back to Projects
        </Button>
      </Container>
    );
  }

  const isOwner = project.role === 'owner';
  const isAdmin = project.role === 'admin' || isOwner;

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/projects')}>
            <ArrowBackIcon />
          </IconButton>
          {editMode ? (
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                value={editedName}
                onChange={(e) => setEditedName(e.target.value)}
                variant="outlined"
                size="small"
                label="Project Name"
              />
              <TextField
                value={editedDescription}
                onChange={(e) => setEditedDescription(e.target.value)}
                variant="outlined"
                size="small"
                label="Description"
                multiline
                rows={2}
                sx={{ minWidth: 300 }}
              />
            </Box>
          ) : (
            <Box>
              <Typography variant="h4">{project.name}</Typography>
              {project.description && (
                <Typography variant="body2" color="text.secondary">
                  {project.description}
                </Typography>
              )}
            </Box>
          )}
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          {editMode ? (
            <>
              <Button
                startIcon={<SaveIcon />}
                variant="contained"
                onClick={handleSaveChanges}
              >
                Save
              </Button>
              <Button
                startIcon={<CancelIcon />}
                onClick={() => {
                  setEditMode(false);
                  setEditedName(project.name);
                  setEditedDescription(project.description || '');
                }}
              >
                Cancel
              </Button>
            </>
          ) : (
            <>
              {isAdmin && (
                <Button
                  startIcon={<EditIcon />}
                  onClick={() => setEditMode(true)}
                >
                  Edit
                </Button>
              )}
              {isOwner && (
                <Button
                  startIcon={<DeleteIcon />}
                  color="error"
                  onClick={() => setDeleteDialogOpen(true)}
                >
                  Delete Project
                </Button>
              )}
            </>
          )}
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper elevation={3}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Overview" />
            <Tab label="Members" icon={<PersonIcon />} iconPosition="start" />
            <Tab label="Activity" icon={<TimelineIcon />} iconPosition="start" />
            <Tab label="Statistics" icon={<AssessmentIcon />} iconPosition="start" />
            <Tab label="Settings" icon={<SettingsIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Project Information</Typography>
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="Organization"
                        secondary={currentOrganization?.name || 'Unknown'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Created"
                        secondary={new Date(project.created_at).toLocaleDateString()}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Your Role"
                        secondary={
                          <Chip
                            label={project.role}
                            size="small"
                            color={project.role === 'owner' ? 'primary' : 'default'}
                          />
                        }
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Quick Stats</Typography>
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="Team Members"
                        secondary={members.length}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Status"
                        secondary={
                          <Chip
                            label={project.is_active ? 'Active' : 'Inactive'}
                            size="small"
                            color={project.is_active ? 'success' : 'default'}
                          />
                        }
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Team Members</Typography>
            {isAdmin && (
              <Button
                startIcon={<PersonAddIcon />}
                variant="contained"
                onClick={() => setAddMemberDialogOpen(true)}
              >
                Add Member
              </Button>
            )}
          </Box>
          
          <List>
            {members.map((member) => (
              <React.Fragment key={member.id}>
                <ListItem>
                  <ListItemAvatar>
                    <Avatar>
                      <PersonIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={member.name || member.email}
                    secondary={member.email}
                  />
                  <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      {isAdmin ? (
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                          <Select
                            value={member.role}
                            onChange={(e) => handleUpdateMemberRole(member.id, e.target.value)}
                            disabled={member.role === 'owner'}
                          >
                            <MenuItem value="owner">Owner</MenuItem>
                            <MenuItem value="admin">Admin</MenuItem>
                            <MenuItem value="member">Member</MenuItem>
                            <MenuItem value="viewer">Viewer</MenuItem>
                          </Select>
                        </FormControl>
                      ) : (
                        <Chip label={member.role} size="small" />
                      )}
                      {isAdmin && member.role !== 'owner' && (
                        <IconButton
                          edge="end"
                          onClick={() => handleRemoveMember(member.id)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      )}
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>Recent Activity</Typography>
          {activity.length > 0 ? (
            <List>
              {activity.map((item, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemText
                      primary={item.description}
                      secondary={`${item.user_name} • ${new Date(item.created_at).toLocaleString()}`}
                    />
                  </ListItem>
                  {index < activity.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No activity recorded yet
            </Typography>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>Project Statistics</Typography>
          {stats ? (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Total Content
                    </Typography>
                    <Typography variant="h4">
                      {stats.total_content || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      This Month
                    </Typography>
                    <Typography variant="h4">
                      {stats.content_this_month || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Team Size
                    </Typography>
                    <Typography variant="h4">
                      {members.length}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Active Days
                    </Typography>
                    <Typography variant="h4">
                      {stats.active_days || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Loading statistics...
            </Typography>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <Typography variant="h6" gutterBottom>Project Settings</Typography>
          <Alert severity="info">
            Project settings configuration coming soon
          </Alert>
        </TabPanel>
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Project</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this project? This action cannot be undone.
            All project data, including content and settings, will be permanently deleted.
          </DialogContentText>
          <DialogContentText sx={{ mt: 2 }}>
            Please type <strong>{project?.name}</strong> to confirm:
          </DialogContentText>
          <TextField
            fullWidth
            variant="outlined"
            value={deleteConfirmation}
            onChange={(e) => setDeleteConfirmation(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteProject}
            color="error"
            variant="contained"
            disabled={deleteConfirmation !== project?.name}
          >
            Delete Project
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Member Dialog */}
      <Dialog open={addMemberDialogOpen} onClose={() => setAddMemberDialogOpen(false)}>
        <DialogTitle>Add Team Member</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Email Address"
            value={newMemberEmail}
            onChange={(e) => setNewMemberEmail(e.target.value)}
            sx={{ mt: 2, mb: 2 }}
          />
          <FormControl fullWidth>
            <InputLabel>Role</InputLabel>
            <Select
              value={newMemberRole}
              onChange={(e) => setNewMemberRole(e.target.value)}
              label="Role"
            >
              <MenuItem value="admin">Admin</MenuItem>
              <MenuItem value="member">Member</MenuItem>
              <MenuItem value="viewer">Viewer</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddMemberDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAddMember}
            variant="contained"
            disabled={!newMemberEmail}
          >
            Add Member
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProjectDetail;