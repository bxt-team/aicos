import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Tabs,
  Tab,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Alert,
  Skeleton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Flag as FlagIcon,
  Assignment as AssignmentIcon,
  Business as BusinessIcon,
  People as PeopleIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { GoalsManagement } from './GoalsManagement';
import { TaskManagement } from './TaskManagement';
import api from '../services/api';

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

interface Project {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  is_active: boolean;
  created_at: string;
  role?: string;
}

interface Department {
  id: string;
  name: string;
  description?: string;
  associated_at: string;
}

interface ProjectStats {
  goals: {
    total: number;
    active: number;
    completed: number;
  };
  tasks: {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
  };
  departments: number;
  team_members: number;
}

export const ProjectDashboard: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useSupabaseAuth();
  const { currentOrganization } = useOrganization();
  const [tabValue, setTabValue] = useState(0);
  const [project, setProject] = useState<Project | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [departmentDialog, setDepartmentDialog] = useState(false);
  const [availableDepartments, setAvailableDepartments] = useState<Department[]>([]);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState('');

  useEffect(() => {
    if (projectId) {
      fetchProjectData();
    }
  }, [projectId]);

  const fetchProjectData = async () => {
    if (!projectId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Fetch project details
      const projectResponse = await api.get(`/api/projects/${projectId}`);
      setProject(projectResponse.data.project);
      
      // Fetch project departments
      const deptResponse = await api.get(`/api/projects/${projectId}/departments`);
      setDepartments(deptResponse.data.departments);
      
      // Fetch project stats
      const statsResponse = await api.get(`/api/projects/${projectId}/stats`);
      const statsData = statsResponse.data.statistics;
      
      // Transform stats to match our interface
      setStats({
        goals: {
          total: statsData.content?.goals || 0,
          active: statsData.content?.active_goals || 0,
          completed: statsData.content?.completed_goals || 0,
        },
        tasks: {
          total: statsData.content?.tasks || 0,
          pending: statsData.content?.pending_tasks || 0,
          in_progress: statsData.content?.in_progress_tasks || 0,
          completed: statsData.content?.completed_tasks || 0,
        },
        departments: deptResponse.data.count || 0,
        team_members: statsData.team?.total_members || 0,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load project data');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableDepartments = async () => {
    if (!currentOrganization || !project) return;
    
    try {
      const response = await api.get(`/api/departments?organization_id=${currentOrganization.id}`);
      // Filter out already associated departments
      const associatedIds = departments.map(d => d.id);
      const available = response.data.filter((d: Department) => !associatedIds.includes(d.id));
      setAvailableDepartments(available);
    } catch (err) {
      console.error('Failed to fetch departments:', err);
    }
  };

  const handleAddDepartment = async () => {
    if (!projectId || !selectedDepartmentId) return;
    
    try {
      await api.post(`/api/projects/${projectId}/departments`, {
        department_id: selectedDepartmentId,
      });
      
      setDepartmentDialog(false);
      setSelectedDepartmentId('');
      fetchProjectData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add department');
    }
  };

  const handleRemoveDepartment = async (departmentId: string) => {
    if (!projectId) return;
    
    if (!window.confirm('Remove this department from the project?')) return;
    
    try {
      await api.delete(`/api/projects/${projectId}/departments/${departmentId}`);
      fetchProjectData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove department');
    }
  };

  const isAdmin = project?.role && ['admin', 'owner'].includes(project.role);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Skeleton variant="text" height={60} />
        <Box display="flex" flexWrap="wrap" gap={3} sx={{ mt: 2 }}>
          {[1, 2, 3, 4].map(i => (
            <Box key={i} flex="1 1 250px">
              <Skeleton variant="rectangular" height={120} />
            </Box>
          ))}
        </Box>
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

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          <DashboardIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          {project.name}
        </Typography>
        {project.description && (
          <Typography variant="body1" color="textSecondary">
            {project.description}
          </Typography>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Stats Overview */}
      <Box display="flex" flexWrap="wrap" gap={3} sx={{ mb: 4 }}>
        <Box flex="1 1 250px">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Goals
                  </Typography>
                  <Typography variant="h4">
                    {stats?.goals.total || 0}
                  </Typography>
                  <Box display="flex" gap={1} mt={1}>
                    <Chip
                      size="small"
                      label={`${stats?.goals.active || 0} active`}
                      color="primary"
                    />
                    <Chip
                      size="small"
                      label={`${stats?.goals.completed || 0} done`}
                      color="success"
                    />
                  </Box>
                </Box>
                <FlagIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box flex="1 1 250px">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Tasks
                  </Typography>
                  <Typography variant="h4">
                    {stats?.tasks.total || 0}
                  </Typography>
                  <Box display="flex" gap={0.5} mt={1} flexWrap="wrap">
                    <Chip
                      size="small"
                      label={`${stats?.tasks.pending || 0}`}
                      icon={<ScheduleIcon />}
                    />
                    <Chip
                      size="small"
                      label={`${stats?.tasks.in_progress || 0}`}
                      color="warning"
                    />
                    <Chip
                      size="small"
                      label={`${stats?.tasks.completed || 0}`}
                      icon={<CheckCircleIcon />}
                      color="success"
                    />
                  </Box>
                </Box>
                <AssignmentIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box flex="1 1 250px">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Departments
                  </Typography>
                  <Typography variant="h4">
                    {stats?.departments || 0}
                  </Typography>
                  {isAdmin && (
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      sx={{ mt: 1 }}
                      onClick={() => {
                        fetchAvailableDepartments();
                        setDepartmentDialog(true);
                      }}
                    >
                      Add
                    </Button>
                  )}
                </Box>
                <BusinessIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box flex="1 1 250px">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Team Members
                  </Typography>
                  <Typography variant="h4">
                    {stats?.team_members || 0}
                  </Typography>
                  <Button
                    size="small"
                    sx={{ mt: 1 }}
                    onClick={() => navigate(`/projects/${projectId}/members`)}
                  >
                    Manage
                  </Button>
                </Box>
                <PeopleIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Tabs */}
      <Paper elevation={3}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={(_, newValue) => setTabValue(newValue)}
            aria-label="project tabs"
          >
            <Tab label="Overview" />
            <Tab label="Goals" />
            <Tab label="Tasks" />
            <Tab label="Departments" />
            <Tab label="Activity" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box display="flex" flexWrap="wrap" gap={3}>
            <Box flex="1 1 300px">
              <Typography variant="h6" gutterBottom>
                Recent Goals
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Feature coming soon...
              </Typography>
            </Box>
            <Box flex="1 1 300px">
              <Typography variant="h6" gutterBottom>
                Recent Tasks
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Feature coming soon...
              </Typography>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <GoalsManagement projectId={projectId} />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <TaskManagement 
            projectId={projectId} 
            onGoToGoals={() => setTabValue(1)} 
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            Associated Departments
          </Typography>
          {departments.length === 0 ? (
            <Typography color="textSecondary">
              No departments associated with this project.
            </Typography>
          ) : (
            <List>
              {departments.map((dept) => (
                <ListItem
                  key={dept.id}
                  secondaryAction={
                    isAdmin && (
                      <Button
                        size="small"
                        color="error"
                        onClick={() => handleRemoveDepartment(dept.id)}
                      >
                        Remove
                      </Button>
                    )
                  }
                >
                  <ListItemAvatar>
                    <Avatar>
                      <BusinessIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={dept.name}
                    secondary={dept.description}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <Typography variant="h6" gutterBottom>
            Project Activity
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Activity timeline coming soon...
          </Typography>
        </TabPanel>
      </Paper>

      {/* Add Department Dialog */}
      <Dialog open={departmentDialog} onClose={() => setDepartmentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Department to Project</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            select
            label="Select Department"
            value={selectedDepartmentId}
            onChange={(e) => setSelectedDepartmentId(e.target.value)}
            margin="normal"
          >
            {availableDepartments.map((dept) => (
              <MenuItem key={dept.id} value={dept.id}>
                {dept.name}
              </MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDepartmentDialog(false)}>Cancel</Button>
          <Button
            onClick={handleAddDepartment}
            variant="contained"
            disabled={!selectedDepartmentId}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};