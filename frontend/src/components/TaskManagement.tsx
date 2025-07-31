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
  Chip,
  Skeleton,
  MenuItem,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  Paper,
  Tooltip,
  Badge,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Assignment as AssignmentIcon,
  Person as PersonIcon,
  SmartToy as SmartToyIcon,
  Flag as FlagIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  PlayArrow as PlayArrowIcon,
  Cancel as CancelIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import api from '../services/api';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

interface Goal {
  id: string;
  title: string;
  project_id: string;
}

interface Member {
  id: string;
  user_id: string;
  role: string;
  email: string;
  full_name?: string;
}

interface Task {
  id: string;
  goal_id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_to_type?: 'member' | 'agent';
  assigned_to_id?: string;
  assigned_to_name?: string;
  created_by_type: string;
  created_by_id?: string;
  created_by_name?: string;
  due_date?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  goal_title?: string;
  project_id?: string;
  project_name?: string;
}

interface TaskHistory {
  id: string;
  task_id: string;
  action: string;
  actor_type: string;
  actor_id?: string;
  actor_name?: string;
  old_value?: any;
  new_value?: any;
  created_at: string;
}

interface TaskManagementProps {
  goalId?: string;
  projectId?: string;
  onGoToGoals?: () => void;
}

export const TaskManagement: React.FC<TaskManagementProps> = ({ goalId, projectId, onGoToGoals }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useSupabaseAuth();
  const { currentOrganization } = useOrganization();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [formData, setFormData] = useState({
    goal_id: goalId || '',
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high' | 'urgent',
    assigned_to_type: '' as 'member' | 'agent' | '',
    assigned_to_id: '',
    due_date: null as Date | null,
  });
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [taskToDelete, setTaskToDelete] = useState<Task | null>(null);
  const [filterGoal, setFilterGoal] = useState<string>(goalId || 'all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterAssignedToMe, setFilterAssignedToMe] = useState(false);
  const [historyDialog, setHistoryDialog] = useState(false);
  const [selectedTaskHistory, setSelectedTaskHistory] = useState<TaskHistory[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    fetchTasks();
    if (!goalId) {
      fetchGoals();
    }
    fetchMembers();
  }, [currentOrganization, goalId, projectId, filterGoal, filterStatus, filterAssignedToMe]);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      let url = '/api/tasks';
      const params = new URLSearchParams();
      
      if (goalId) {
        params.append('goal_id', goalId);
      } else if (filterGoal !== 'all') {
        params.append('goal_id', filterGoal);
      } else if (projectId) {
        params.append('project_id', projectId);
      }
      
      if (filterStatus !== 'all') {
        params.append('status', filterStatus);
      }
      
      if (filterAssignedToMe) {
        params.append('assigned_to_me', 'true');
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await api.get(url);
      setTasks(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToFetch', { resource: t('task.tasks').toLowerCase() }));
    } finally {
      setLoading(false);
    }
  };

  const fetchGoals = async () => {
    try {
      let url = '/api/goals';
      if (projectId) {
        url += `?project_id=${projectId}`;
      }
      const response = await api.get(url);
      setGoals(response.data);
    } catch (err) {
      console.error('Failed to fetch goals:', err);
    }
  };

  const fetchMembers = async () => {
    if (!currentOrganization) return;
    
    try {
      const response = await api.get(`/api/organizations/${currentOrganization.id}/members`);
      setMembers(response.data);
    } catch (err) {
      console.error('Failed to fetch members:', err);
    }
  };

  const fetchTaskHistory = async (taskId: string) => {
    setLoadingHistory(true);
    try {
      const response = await api.get(`/api/tasks/${taskId}/history`);
      setSelectedTaskHistory(response.data);
      setHistoryDialog(true);
    } catch (err) {
      console.error('Failed to fetch task history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleOpenDialog = (task?: Task) => {
    if (task) {
      setEditingTask(task);
      setFormData({
        goal_id: task.goal_id,
        title: task.title,
        description: task.description || '',
        priority: task.priority,
        assigned_to_type: task.assigned_to_type || '',
        assigned_to_id: task.assigned_to_id || '',
        due_date: task.due_date ? new Date(task.due_date) : null,
      });
    } else {
      setEditingTask(null);
      setFormData({
        goal_id: goalId || (filterGoal === 'all' ? '' : filterGoal),
        title: '',
        description: '',
        priority: 'medium',
        assigned_to_type: '',
        assigned_to_id: '',
        due_date: null,
      });
    }
    setFormErrors({});
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingTask(null);
    setFormData({
      goal_id: goalId || '',
      title: '',
      description: '',
      priority: 'medium',
      assigned_to_type: '',
      assigned_to_id: '',
      due_date: null,
    });
    setFormErrors({});
  };

  const validateForm = () => {
    const errors: { [key: string]: string } = {};
    
    if (!editingTask && !formData.goal_id) {
      errors.goal_id = 'Goal is required';
    }
    
    if (!formData.title.trim()) {
      errors.title = 'Task title is required';
    } else if (formData.title.length > 200) {
      errors.title = 'Task title must be less than 200 characters';
    }
    
    if (formData.assigned_to_type && !formData.assigned_to_id) {
      errors.assigned_to_id = 'Please select who to assign to';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    try {
      if (editingTask) {
        // Update existing task
        const updateData: any = {
          title: formData.title,
          description: formData.description || undefined,
          priority: formData.priority,
          due_date: formData.due_date?.toISOString().split('T')[0] || undefined,
        };
        
        if (formData.assigned_to_type && formData.assigned_to_id) {
          updateData.assigned_to_type = formData.assigned_to_type;
          updateData.assigned_to_id = formData.assigned_to_id;
        } else {
          updateData.assigned_to_type = null;
          updateData.assigned_to_id = null;
        }
        
        await api.patch(`/api/tasks/${editingTask.id}`, updateData);
      } else {
        // Create new task
        const createData: any = {
          goal_id: formData.goal_id,
          title: formData.title,
          description: formData.description || undefined,
          priority: formData.priority,
          due_date: formData.due_date?.toISOString().split('T')[0] || undefined,
        };
        
        if (formData.assigned_to_type && formData.assigned_to_id) {
          createData.assigned_to_type = formData.assigned_to_type;
          createData.assigned_to_id = formData.assigned_to_id;
        }
        
        await api.post('/api/tasks', createData);
      }
      
      handleCloseDialog();
      fetchTasks();
    } catch (err: any) {
      setFormErrors({
        submit: err.response?.data?.detail || 'Failed to save task',
      });
    }
  };

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    try {
      await api.patch(`/api/tasks/${taskId}`, { status: newStatus });
      fetchTasks();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToUpdate', { resource: t('task.taskStatus').toLowerCase() }));
    }
  };

  const handleDeleteClick = (task: Task) => {
    setTaskToDelete(task);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!taskToDelete) return;

    try {
      await api.delete(`/api/tasks/${taskToDelete.id}`);
      setDeleteConfirmOpen(false);
      setTaskToDelete(null);
      fetchTasks();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToDelete', { resource: t('task.task').toLowerCase() }));
      setDeleteConfirmOpen(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'primary';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <ScheduleIcon fontSize="small" />;
      case 'in_progress':
        return <PlayArrowIcon fontSize="small" />;
      case 'completed':
        return <CheckCircleIcon fontSize="small" />;
      case 'cancelled':
        return <CancelIcon fontSize="small" />;
      default:
        return null;
    }
  };

  const renderTaskCard = (task: Task) => (
    <Card key={task.id} sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Typography variant="h6" gutterBottom>
              {task.title}
            </Typography>
            <Box display="flex" gap={1} mb={1} flexWrap="wrap">
              <Chip
                icon={getStatusIcon(task.status) || undefined}
                label={task.status.replace('_', ' ')}
                size="small"
                color={task.status === 'completed' ? 'success' : 'default'}
              />
              <Chip
                label={task.priority}
                size="small"
                color={getPriorityColor(task.priority)}
              />
              {task.assigned_to_name && (
                <Chip
                  icon={task.assigned_to_type === 'agent' ? <SmartToyIcon /> : <PersonIcon />}
                  label={task.assigned_to_name}
                  size="small"
                  variant="outlined"
                />
              )}
              {task.due_date && (
                <Chip
                  icon={<ScheduleIcon />}
                  label={new Date(task.due_date).toLocaleDateString()}
                  size="small"
                  variant="outlined"
                  color={new Date(task.due_date) < new Date() && task.status !== 'completed' ? 'error' : 'default'}
                />
              )}
            </Box>
            {task.description && (
              <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                {task.description.split('\n')[0]}
              </Typography>
            )}
            <Typography variant="caption" color="textSecondary">
              {task.goal_title} {task.project_name && `• ${task.project_name}`}
            </Typography>
          </Box>
          <Box>
            <IconButton
              size="small"
              onClick={() => handleOpenDialog(task)}
              title="Edit task"
            >
              <EditIcon />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => fetchTaskHistory(task.id)}
              title="View history"
            >
              <HistoryIcon />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => handleDeleteClick(task)}
              title="Delete task"
            >
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>
        {viewMode === 'list' && (
          <Box mt={2} display="flex" gap={1}>
            <Button
              size="small"
              disabled={task.status === 'pending'}
              onClick={() => handleStatusChange(task.id, 'pending')}
            >
              Pending
            </Button>
            <Button
              size="small"
              disabled={task.status === 'in_progress'}
              onClick={() => handleStatusChange(task.id, 'in_progress')}
            >
              In Progress
            </Button>
            <Button
              size="small"
              disabled={task.status === 'completed'}
              onClick={() => handleStatusChange(task.id, 'completed')}
            >
              Complete
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderKanbanColumn = (status: string, statusTasks: Task[]) => (
    <Paper sx={{ p: 2, bgcolor: 'grey.50', minHeight: 400 }}>
      <Typography variant="h6" gutterBottom>
        {status.replace('_', ' ').toUpperCase()}
        <Chip label={statusTasks.length} size="small" sx={{ ml: 1 }} />
      </Typography>
      {statusTasks.map((task) => renderTaskCard(task))}
    </Paper>
  );

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          <AssignmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          {t('task.tasks')}
        </Typography>
        <Box display="flex" gap={1}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, value) => value && setViewMode(value)}
            size="small"
          >
            <ToggleButton value="list">
              <ViewListIcon />
            </ToggleButton>
            <ToggleButton value="kanban">
              <ViewModuleIcon />
            </ToggleButton>
          </ToggleButtonGroup>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            disabled={goalId ? false : goals.length === 0}
          >
            {t('task.addTask', 'Add Task')}
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Box mb={3} display="flex" gap={2} flexWrap="wrap">
        {!goalId && (
          <TextField
            select
            label={t('task.goal', 'Goal')}
            value={filterGoal}
            onChange={(e) => setFilterGoal(e.target.value)}
            size="small"
            sx={{ minWidth: 200 }}
          >
            <MenuItem value="all">All Goals</MenuItem>
            {goals.map((goal) => (
              <MenuItem key={goal.id} value={goal.id}>
                {goal.title}
              </MenuItem>
            ))}
          </TextField>
        )}
        {viewMode === 'list' && (
          <TextField
            select
            label={t('common.status')}
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            size="small"
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="in_progress">In Progress</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
          </TextField>
        )}
        <Button
          variant={filterAssignedToMe ? 'contained' : 'outlined'}
          onClick={() => setFilterAssignedToMe(!filterAssignedToMe)}
          size="small"
        >
          Assigned to Me
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Grid container spacing={2}>
          {[1, 2, 3].map((i) => (
            <Grid size={{ xs: 12 }} key={i}>
              <Skeleton variant="rectangular" height={150} />
            </Grid>
          ))}
        </Grid>
      ) : tasks.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign="center">
              <Typography color="textSecondary" gutterBottom>
                {goals.length === 0
                  ? 'No goals available. Please go to "Goals" in the side menu to create a goal first, then you can add tasks.'
                  : 'No tasks found. Click "Add Task" to get started.'}
              </Typography>
              {goals.length === 0 && projectId && (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => navigate(`/projects/${projectId}/goals`)}
                  sx={{ mt: 2 }}
                  startIcon={<FlagIcon />}
                >
                  Go to Goals
                </Button>
              )}
            </Box>
          </CardContent>
        </Card>
      ) : viewMode === 'list' ? (
        <Box>
          {tasks.map((task) => renderTaskCard(task))}
        </Box>
      ) : (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 3 }}>
            {renderKanbanColumn('pending', tasks.filter(t => t.status === 'pending'))}
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            {renderKanbanColumn('in_progress', tasks.filter(t => t.status === 'in_progress'))}
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            {renderKanbanColumn('completed', tasks.filter(t => t.status === 'completed'))}
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            {renderKanbanColumn('cancelled', tasks.filter(t => t.status === 'cancelled'))}
          </Grid>
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingTask ? 'Edit Task' : 'Create New Task'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {!editingTask && !goalId && (
              <TextField
                fullWidth
                select
                label={t('task.goal', 'Goal')}
                value={formData.goal_id}
                onChange={(e) => setFormData({ ...formData, goal_id: e.target.value })}
                error={!!formErrors.goal_id}
                helperText={formErrors.goal_id}
                margin="normal"
                required
              >
                {goals.map((goal) => (
                  <MenuItem key={goal.id} value={goal.id}>
                    {goal.title}
                  </MenuItem>
                ))}
              </TextField>
            )}
            <TextField
              fullWidth
              label={t('task.taskTitle')}
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              error={!!formErrors.title}
              helperText={formErrors.title}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label={t('common.description')}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
            <TextField
              fullWidth
              select
              label={t('task.taskPriority')}
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
              margin="normal"
            >
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="urgent">Urgent</MenuItem>
            </TextField>
            <TextField
              fullWidth
              select
              label={t('task.assignTo', 'Assign To')}
              value={formData.assigned_to_type}
              onChange={(e) => setFormData({ 
                ...formData, 
                assigned_to_type: e.target.value as any,
                assigned_to_id: ''
              })}
              margin="normal"
            >
              <MenuItem value="">Unassigned</MenuItem>
              <MenuItem value="member">Member</MenuItem>
              <MenuItem value="agent">AI Agent</MenuItem>
            </TextField>
            {formData.assigned_to_type === 'member' && (
              <TextField
                fullWidth
                select
                label={t('task.selectMember', 'Select Member')}
                value={formData.assigned_to_id}
                onChange={(e) => setFormData({ ...formData, assigned_to_id: e.target.value })}
                error={!!formErrors.assigned_to_id}
                helperText={formErrors.assigned_to_id}
                margin="normal"
              >
                {members.map((member) => (
                  <MenuItem key={member.user_id} value={member.user_id}>
                    {member.full_name || member.email} ({member.role})
                  </MenuItem>
                ))}
              </TextField>
            )}
            {formData.assigned_to_type === 'agent' && (
              <TextField
                fullWidth
                label={t('task.agentId', 'Agent ID')}
                value={formData.assigned_to_id}
                onChange={(e) => setFormData({ ...formData, assigned_to_id: e.target.value })}
                error={!!formErrors.assigned_to_id}
                helperText={formErrors.assigned_to_id || 'Enter the AI agent identifier'}
                margin="normal"
              />
            )}
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label={t('task.taskDueDate')}
                value={formData.due_date}
                onChange={(date) => setFormData({ ...formData, due_date: date })}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    margin: 'normal',
                  },
                }}
              />
            </LocalizationProvider>
            {formErrors.submit && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {formErrors.submit}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>{t('common.cancel')}</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingTask ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* History Dialog */}
      <Dialog open={historyDialog} onClose={() => setHistoryDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Task History</DialogTitle>
        <DialogContent>
          {loadingHistory ? (
            <Box p={3}>
              <Skeleton variant="text" />
              <Skeleton variant="text" />
              <Skeleton variant="text" />
            </Box>
          ) : (
            <List>
              {selectedTaskHistory.map((history, index) => (
                <React.Fragment key={history.id}>
                  {index > 0 && <Divider />}
                  <ListItem>
                    <ListItemAvatar>
                      <Avatar>
                        {history.actor_type === 'agent' ? <SmartToyIcon /> : <PersonIcon />}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box>
                          <strong>{history.actor_name || 'Unknown'}</strong> {history.action}
                          {history.action === 'updated' && history.old_value && (
                            <Box component="span" ml={1}>
                              {Object.entries(history.old_value).map(([key, value]: [string, any]) => (
                                <Chip
                                  key={key}
                                  label={`${key}: ${value.old} → ${value.new}`}
                                  size="small"
                                  sx={{ ml: 0.5 }}
                                />
                              ))}
                            </Box>
                          )}
                        </Box>
                      }
                      secondary={new Date(history.created_at).toLocaleString()}
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialog(false)}>{t('common.close')}</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the task "{taskToDelete?.title}"?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};