import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Typography,
  Alert,
  LinearProgress,
  Skeleton,
  MenuItem,
  Chip,
  List,
  ListItem,
  ListItemText,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Flag as FlagIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import api from '../services/api';

interface Project {
  id: string;
  name: string;
}

interface Goal {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  target_date?: string;
  status: 'active' | 'completed' | 'archived';
  progress: number;
  created_at: string;
  updated_at: string;
  task_count: number;
  completed_task_count: number;
  project_name?: string;
}

interface GoalsManagementProps {
  projectId?: string;
}

export const GoalsManagement: React.FC<GoalsManagementProps> = ({ projectId }) => {
  const { user } = useSupabaseAuth();
  const { currentOrganization } = useOrganization();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [formData, setFormData] = useState({
    project_id: projectId || '',
    title: '',
    description: '',
    target_date: null as Date | null,
    status: 'active' as 'active' | 'completed' | 'archived',
    progress: 0,
  });
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [goalToDelete, setGoalToDelete] = useState<Goal | null>(null);
  const [filterProject, setFilterProject] = useState<string>(projectId || 'all');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    if (currentOrganization || projectId) {
      fetchGoals();
      if (!projectId) {
        fetchProjects();
      }
    }
  }, [currentOrganization, projectId, filterProject, filterStatus]);

  const fetchGoals = async () => {
    setLoading(true);
    setError(null);
    try {
      let url = '/api/goals';
      const params = new URLSearchParams();
      
      if (projectId) {
        params.append('project_id', projectId);
      } else if (filterProject !== 'all') {
        params.append('project_id', filterProject);
      }
      
      if (filterStatus !== 'all') {
        params.append('status', filterStatus);
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await api.get(url);
      setGoals(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch goals');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    if (!currentOrganization) return;
    
    try {
      const response = await api.get(`/api/projects?organization_id=${currentOrganization.id}`);
      setProjects(response.data.projects || []);
    } catch (err) {
      console.error('Failed to fetch projects:', err);
    }
  };

  const handleOpenDialog = (goal?: Goal) => {
    if (goal) {
      setEditingGoal(goal);
      setFormData({
        project_id: goal.project_id,
        title: goal.title,
        description: goal.description || '',
        target_date: goal.target_date ? new Date(goal.target_date) : null,
        status: goal.status,
        progress: goal.progress,
      });
    } else {
      setEditingGoal(null);
      setFormData({
        project_id: projectId || filterProject === 'all' ? '' : filterProject,
        title: '',
        description: '',
        target_date: null,
        status: 'active',
        progress: 0,
      });
    }
    setFormErrors({});
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingGoal(null);
    setFormData({
      project_id: projectId || '',
      title: '',
      description: '',
      target_date: null,
      status: 'active',
      progress: 0,
    });
    setFormErrors({});
  };

  const validateForm = () => {
    const errors: { [key: string]: string } = {};
    
    if (!editingGoal && !formData.project_id) {
      errors.project_id = 'Project is required';
    }
    
    if (!formData.title.trim()) {
      errors.title = 'Goal title is required';
    } else if (formData.title.length > 200) {
      errors.title = 'Goal title must be less than 200 characters';
    }
    
    if (formData.progress < 0 || formData.progress > 100) {
      errors.progress = 'Progress must be between 0 and 100';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    try {
      if (editingGoal) {
        // Update existing goal
        const updateData: any = {
          title: formData.title,
          description: formData.description || undefined,
          target_date: formData.target_date?.toISOString().split('T')[0] || undefined,
          status: formData.status,
          progress: formData.progress,
        };
        
        await api.patch(`/api/goals/${editingGoal.id}`, updateData);
      } else {
        // Create new goal
        const createData = {
          project_id: formData.project_id,
          title: formData.title,
          description: formData.description || undefined,
          target_date: formData.target_date?.toISOString().split('T')[0] || undefined,
        };
        
        await api.post('/api/goals', createData);
      }
      
      handleCloseDialog();
      fetchGoals();
    } catch (err: any) {
      setFormErrors({
        submit: err.response?.data?.detail || 'Failed to save goal',
      });
    }
  };

  const handleDeleteClick = (goal: Goal) => {
    setGoalToDelete(goal);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!goalToDelete) return;

    try {
      await api.delete(`/api/goals/${goalToDelete.id}`);
      setDeleteConfirmOpen(false);
      setGoalToDelete(null);
      fetchGoals();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete goal');
      setDeleteConfirmOpen(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'primary';
      case 'completed':
        return 'success';
      case 'archived':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <ScheduleIcon fontSize="small" />;
      case 'completed':
        return <CheckCircleIcon fontSize="small" />;
      default:
        return <FlagIcon fontSize="small" />;
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          <FlagIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Goals & Key Results
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          disabled={projectId ? false : projects.length === 0}
        >
          Add Goal
        </Button>
      </Box>

      {/* Filters */}
      {!projectId && (
        <Box mb={3} display="flex" gap={2}>
          <TextField
            select
            label="Project"
            value={filterProject}
            onChange={(e) => setFilterProject(e.target.value)}
            size="small"
            sx={{ minWidth: 200 }}
          >
            <MenuItem value="all">All Projects</MenuItem>
            {projects.map((project) => (
              <MenuItem key={project.id} value={project.id}>
                {project.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label="Status"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            size="small"
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="archived">Archived</MenuItem>
          </TextField>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Grid container spacing={2}>
          {[1, 2, 3].map((i) => (
            <Grid size={{ xs: 12, md: 6 }} key={i}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" width="60%" height={32} />
                  <Skeleton variant="text" width="100%" />
                  <Skeleton variant="rectangular" height={20} sx={{ mt: 2 }} />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : goals.length === 0 ? (
        <Card>
          <CardContent>
            <Typography color="textSecondary" align="center">
              {projects.length === 0
                ? 'No projects available. Create a project first to add goals.'
                : 'No goals created yet. Click "Add Goal" to get started.'}
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {goals.map((goal) => (
            <Grid size={{ xs: 12, md: 6 }} key={goal.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                    <Box flex={1}>
                      <Typography variant="h6" gutterBottom>
                        {goal.title}
                      </Typography>
                      <Box display="flex" gap={1} mb={1}>
                        <Chip
                          icon={getStatusIcon(goal.status)}
                          label={goal.status}
                          size="small"
                          color={getStatusColor(goal.status)}
                        />
                        {!projectId && goal.project_name && (
                          <Chip
                            label={goal.project_name}
                            size="small"
                            variant="outlined"
                          />
                        )}
                        {goal.target_date && (
                          <Chip
                            icon={<ScheduleIcon />}
                            label={new Date(goal.target_date).toLocaleDateString()}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                    <Box>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(goal)}
                        title="Edit goal"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteClick(goal)}
                        title="Delete goal"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Box>
                  
                  {goal.description && (
                    <Typography variant="body2" color="textSecondary" paragraph>
                      {goal.description}
                    </Typography>
                  )}
                  
                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2" color="textSecondary">
                        Progress
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {goal.progress}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={goal.progress}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                  
                  <Box display="flex" alignItems="center" gap={1}>
                    <AssignmentIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="textSecondary">
                      {goal.completed_task_count} of {goal.task_count} tasks completed
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingGoal ? 'Edit Goal' : 'Create New Goal'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {!editingGoal && !projectId && (
              <TextField
                fullWidth
                select
                label="Project"
                value={formData.project_id}
                onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                error={!!formErrors.project_id}
                helperText={formErrors.project_id}
                margin="normal"
                required
              >
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </TextField>
            )}
            <TextField
              fullWidth
              label="Goal Title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              error={!!formErrors.title}
              helperText={formErrors.title}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Target Date"
                value={formData.target_date}
                onChange={(date) => setFormData({ ...formData, target_date: date })}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    margin: 'normal',
                  },
                }}
              />
            </LocalizationProvider>
            {editingGoal && (
              <>
                <TextField
                  fullWidth
                  select
                  label="Status"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                  margin="normal"
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="archived">Archived</MenuItem>
                </TextField>
                <TextField
                  fullWidth
                  label="Progress (%)"
                  type="number"
                  value={formData.progress}
                  onChange={(e) => setFormData({ ...formData, progress: parseInt(e.target.value) || 0 })}
                  error={!!formErrors.progress}
                  helperText={formErrors.progress}
                  margin="normal"
                  inputProps={{ min: 0, max: 100 }}
                />
              </>
            )}
            {formErrors.submit && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {formErrors.submit}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingGoal ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the goal "{goalToDelete?.title}"?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This will also delete all {goalToDelete?.task_count || 0} associated tasks.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};