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
  CircularProgress,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Checkbox,
  Rating,
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
  AutoAwesome as AutoAwesomeIcon,
  Feedback as FeedbackIcon,
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
  const [promptTemplateOpen, setPromptTemplateOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(0);
  const [customPrompt, setCustomPrompt] = useState('');
  const [suggestDialogOpen, setSuggestDialogOpen] = useState(false);
  const [suggestedTasks, setSuggestedTasks] = useState<any[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(new Set());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [taskRatings, setTaskRatings] = useState<{ [key: number]: number }>({});
  const [taskFeedback, setTaskFeedback] = useState<{ [key: number]: string }>({});
  const [feedbackSummary, setFeedbackSummary] = useState<any>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [selectedGoalForAI, setSelectedGoalForAI] = useState<string>('');

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

  const promptTemplates = [
    {
      name: 'Goal Achievement Tasks',
      description: 'Break down a goal into specific, actionable tasks with clear deliverables',
      prompt: 'Generate tasks that systematically work towards achieving the goal. Focus on concrete deliverables, clear action items, and logical progression. Include tasks for planning, execution, validation, and documentation.',
    },
    {
      name: 'Quick Wins & Milestones',
      description: 'Create tasks that deliver quick wins and measurable milestones',
      prompt: 'Generate tasks that provide quick wins and early momentum. Include milestone tasks that show clear progress, build confidence, and validate the approach. Balance quick wins with foundational work.',
    },
    {
      name: 'Risk Mitigation & Dependencies',
      description: 'Generate tasks that address risks, dependencies, and potential blockers',
      prompt: 'Generate tasks that identify and mitigate risks, manage dependencies, and prevent blockers. Include tasks for research, validation, contingency planning, and coordination with stakeholders.',
    },
  ];

  const handleOpenPromptDialog = () => {
    const currentGoalId = goalId || (filterGoal !== 'all' ? filterGoal : '');
    setSelectedGoalForAI(currentGoalId);
    setCustomPrompt(promptTemplates[selectedTemplate].prompt);
    setPromptTemplateOpen(true);
  };

  const handleSuggestTasks = async () => {
    if (!selectedGoalForAI) {
      setError('Please select a goal first');
      return;
    }

    setPromptTemplateOpen(false);
    setLoadingSuggestions(true);
    setSuggestDialogOpen(true);
    setError(null);
    setShowFeedbackForm(false);
    setTaskRatings({});
    setTaskFeedback({});

    try {
      // First fetch feedback summary
      try {
        const summaryResponse = await api.get(`/api/tasks/feedback/summary?goal_id=${selectedGoalForAI}`);
        setFeedbackSummary(summaryResponse.data);
      } catch (err) {
        // Continue without feedback summary
      }

      const response = await api.post('/api/tasks/suggest', {
        goal_id: selectedGoalForAI,
        custom_prompt: customPrompt,
        session_id: sessionId,
      });

      setSuggestedTasks(response.data.tasks || []);
      setSessionId(response.data.session_id || null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate task suggestions');
      setSuggestDialogOpen(false);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleToggleSuggestion = (index: number) => {
    const newSelection = new Set(selectedSuggestions);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedSuggestions(newSelection);
  };

  const handleSubmitFeedback = async () => {
    if (!sessionId || !selectedGoalForAI) return;

    try {
      const feedbackData = suggestedTasks.map((task, index) => ({
        task_index: index,
        feedback_type: selectedSuggestions.has(index) ? 'accepted' : 'rejected',
        rating: taskRatings[index] || undefined,
        feedback_text: taskFeedback[index] || undefined,
      }));

      await api.post('/api/tasks/suggest/feedback', {
        goal_id: selectedGoalForAI,
        session_id: sessionId,
        suggested_tasks: suggestedTasks,
        feedback: feedbackData,
      });

      setShowFeedbackForm(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    }
  };

  const handleApplySuggestions = async () => {
    const tasksToCreate = Array.from(selectedSuggestions).map(index => suggestedTasks[index]);
    
    // Submit feedback before creating tasks
    if (showFeedbackForm) {
      await handleSubmitFeedback();
    }
    
    for (const task of tasksToCreate) {
      try {
        await api.post('/api/tasks', {
          goal_id: selectedGoalForAI,
          title: task.title,
          description: task.description,
          priority: task.priority,
          assigned_to_type: task.suggested_assignee_type || undefined,
          assigned_to_id: task.suggested_assignee_id || undefined,
          due_date: task.estimated_duration ? calculateDueDate(task.estimated_duration) : undefined,
        });
      } catch (err: any) {
        setError(`Failed to create task "${task.title}": ${err.response?.data?.detail || err.message}`);
      }
    }

    setSuggestDialogOpen(false);
    setSuggestedTasks([]);
    setSelectedSuggestions(new Set());
    setSessionId(null);
    fetchTasks();
  };

  const calculateDueDate = (duration: string): string | null => {
    const now = new Date();
    const match = duration.match(/(\d+)\s*(hour|day|week|month)/i);
    
    if (!match) return null;
    
    const [, amount, unit] = match;
    const num = parseInt(amount);
    
    switch (unit.toLowerCase()) {
      case 'hour':
      case 'hours':
        now.setHours(now.getHours() + num);
        break;
      case 'day':
      case 'days':
        now.setDate(now.getDate() + num);
        break;
      case 'week':
      case 'weeks':
        now.setDate(now.getDate() + (num * 7));
        break;
      case 'month':
      case 'months':
        now.setMonth(now.getMonth() + num);
        break;
    }
    
    return now.toISOString().split('T')[0];
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
            startIcon={<AutoAwesomeIcon />}
            onClick={handleOpenPromptDialog}
            color="secondary"
            disabled={goals.length === 0}
          >
            AI Generate Tasks
          </Button>
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
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rectangular" height={150} />
          ))}
        </Box>
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
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' },
          gap: 2 
        }}>
          <Box>
            {renderKanbanColumn('pending', tasks.filter(t => t.status === 'pending'))}
          </Box>
          <Box>
            {renderKanbanColumn('in_progress', tasks.filter(t => t.status === 'in_progress'))}
          </Box>
          <Box>
            {renderKanbanColumn('completed', tasks.filter(t => t.status === 'completed'))}
          </Box>
          <Box>
            {renderKanbanColumn('cancelled', tasks.filter(t => t.status === 'cancelled'))}
          </Box>
        </Box>
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

      {/* Prompt Template Dialog */}
      <Dialog
        open={promptTemplateOpen}
        onClose={() => setPromptTemplateOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <AutoAwesomeIcon color="primary" />
            Choose AI Task Generation Template
          </Box>
        </DialogTitle>
        <DialogContent>
          {!selectedGoalForAI && (
            <Box mb={3}>
              <TextField
                fullWidth
                select
                label="Select Goal"
                value={selectedGoalForAI}
                onChange={(e) => setSelectedGoalForAI(e.target.value)}
                helperText="Please select a goal for which you want to generate tasks"
                error={!selectedGoalForAI}
              >
                {goals.map((goal) => (
                  <MenuItem key={goal.id} value={goal.id}>
                    {goal.title}
                  </MenuItem>
                ))}
              </TextField>
            </Box>
          )}
          <FormControl component="fieldset" sx={{ width: '100%' }}>
            <FormLabel component="legend" sx={{ mb: 2 }}>
              Select a template or customize the prompt for generating tasks:
            </FormLabel>
            <RadioGroup
              value={selectedTemplate}
              onChange={(e) => {
                const newTemplate = parseInt(e.target.value);
                setSelectedTemplate(newTemplate);
                setCustomPrompt(promptTemplates[newTemplate].prompt);
              }}
            >
              {promptTemplates.map((template, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, border: selectedTemplate === index ? 2 : 1, borderColor: selectedTemplate === index ? 'primary.main' : 'divider' }}>
                  <FormControlLabel
                    value={index}
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {template.name}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {template.description}
                        </Typography>
                      </Box>
                    }
                  />
                </Paper>
              ))}
            </RadioGroup>
          </FormControl>
          
          <Box mt={3}>
            <Typography variant="subtitle1" gutterBottom>
              Customize the prompt:
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="Enter your custom prompt for task generation..."
              helperText="You can modify the prompt to better suit your specific needs and context"
              sx={{ mt: 1 }}
            />
          </Box>
          
          <Alert severity="info" sx={{ mt: 2 }}>
            The AI will analyze the selected goal and generate specific tasks based on your prompt.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPromptTemplateOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSuggestTasks}
            variant="contained"
            startIcon={<AutoAwesomeIcon />}
            disabled={!selectedGoalForAI || !customPrompt.trim()}
          >
            Generate Tasks
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Suggestions Dialog */}
      <Dialog 
        open={suggestDialogOpen} 
        onClose={() => !loadingSuggestions && setSuggestDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <AutoAwesomeIcon color="primary" />
            AI Task Suggestions
          </Box>
        </DialogTitle>
        <DialogContent>
          {loadingSuggestions ? (
            <Box py={4} textAlign="center">
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 3,
                }}
              >
                {/* Animated brain/thinking icon */}
                <Box
                  sx={{
                    position: 'relative',
                    width: 80,
                    height: 80,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <AutoAwesomeIcon
                    sx={{
                      fontSize: 40,
                      color: 'primary.main',
                      animation: 'pulse 2s ease-in-out infinite',
                      '@keyframes pulse': {
                        '0%': {
                          opacity: 0.4,
                          transform: 'scale(1)',
                        },
                        '50%': {
                          opacity: 1,
                          transform: 'scale(1.1)',
                        },
                        '100%': {
                          opacity: 0.4,
                          transform: 'scale(1)',
                        },
                      },
                    }}
                  />
                  <CircularProgress
                    size={80}
                    thickness={2}
                    sx={{
                      position: 'absolute',
                      color: 'primary.light',
                    }}
                  />
                </Box>
                
                <Box textAlign="center">
                  <Typography variant="h6" gutterBottom>
                    AI is thinking...
                  </Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    Analyzing the goal and generating specific tasks
                  </Typography>
                  
                  {/* Animated thinking dots */}
                  <Typography
                    variant="body2"
                    color="primary"
                    sx={{
                      '& .dot': {
                        display: 'inline-block',
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        backgroundColor: 'primary.main',
                        margin: '0 4px',
                        animation: 'thinking 1.4s infinite ease-in-out',
                      },
                      '& .dot:nth-of-type(1)': {
                        animationDelay: '-0.32s',
                      },
                      '& .dot:nth-of-type(2)': {
                        animationDelay: '-0.16s',
                      },
                      '@keyframes thinking': {
                        '0%, 80%, 100%': {
                          transform: 'scale(0.8)',
                          opacity: 0.5,
                        },
                        '40%': {
                          transform: 'scale(1)',
                          opacity: 1,
                        },
                      },
                    }}
                  >
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </Typography>
                </Box>
              </Box>
            </Box>
          ) : suggestedTasks.length > 0 ? (
            <>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Select the tasks you'd like to add:
              </Typography>
              
              {/* Feedback Summary */}
              {feedbackSummary && feedbackSummary.total_feedback > 0 && (
                <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
                  <Typography variant="subtitle2" gutterBottom>
                    <FeedbackIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                    Previous Feedback Summary
                  </Typography>
                  <Box display="flex" gap={2} alignItems="center">
                    <Rating value={feedbackSummary.average_rating} readOnly size="small" />
                    <Typography variant="body2" color="textSecondary">
                      {feedbackSummary.average_rating.toFixed(1)}/5 ({feedbackSummary.total_feedback} reviews)
                    </Typography>
                  </Box>
                </Paper>
              )}
              
              <List>
                {suggestedTasks.map((task, index) => (
                  <Card key={index} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box display="flex" alignItems="flex-start">
                        <Checkbox
                          checked={selectedSuggestions.has(index)}
                          onChange={() => handleToggleSuggestion(index)}
                          sx={{ mt: -1 }}
                        />
                        <Box flex={1}>
                          <Typography variant="h6" gutterBottom>
                            {task.title}
                          </Typography>
                          <Typography variant="body2" paragraph>
                            {task.description}
                          </Typography>
                          <Box display="flex" gap={1} mb={1} flexWrap="wrap">
                            <Chip 
                              label={task.priority} 
                              size="small" 
                              color={getPriorityColor(task.priority)}
                            />
                            {task.estimated_duration && (
                              <Chip 
                                label={`Duration: ${task.estimated_duration}`} 
                                size="small" 
                                variant="outlined"
                              />
                            )}
                            {task.suggested_assignee_type && (
                              <Chip 
                                label={`Assign to: ${task.suggested_assignee_type}`} 
                                size="small" 
                                variant="outlined"
                              />
                            )}
                          </Box>
                          <Typography variant="caption" color="textSecondary">
                            <strong>Rationale:</strong> {task.rationale}
                          </Typography>
                          
                          {/* Feedback Form */}
                          {showFeedbackForm && (
                            <Box mt={2} p={2} bgcolor="background.default" borderRadius={1}>
                              <Typography variant="subtitle2" gutterBottom>
                                Rate this suggestion:
                              </Typography>
                              <Rating
                                value={taskRatings[index] || 0}
                                onChange={(event, newValue) => {
                                  setTaskRatings({ ...taskRatings, [index]: newValue || 0 });
                                }}
                                size="small"
                              />
                              <TextField
                                fullWidth
                                size="small"
                                placeholder="Optional feedback..."
                                value={taskFeedback[index] || ''}
                                onChange={(e) => {
                                  setTaskFeedback({ ...taskFeedback, [index]: e.target.value });
                                }}
                                sx={{ mt: 1 }}
                                multiline
                                rows={2}
                              />
                            </Box>
                          )}
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </List>
              
              {/* Show/Hide Feedback Toggle */}
              {!showFeedbackForm && (
                <Box textAlign="center" mt={2}>
                  <Button
                    startIcon={<FeedbackIcon />}
                    onClick={() => setShowFeedbackForm(true)}
                    size="small"
                  >
                    Provide Feedback
                  </Button>
                </Box>
              )}
            </>
          ) : (
            <Alert severity="info">
              No suggestions generated. Please try again.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setSuggestDialogOpen(false);
            setSessionId(null);
            setShowFeedbackForm(false);
          }} disabled={loadingSuggestions}>
            Cancel
          </Button>
          {showFeedbackForm && (
            <Button 
              onClick={handleSubmitFeedback}
              disabled={loadingSuggestions}
              startIcon={<FeedbackIcon />}
            >
              Submit Feedback Only
            </Button>
          )}
          <Button 
            onClick={handleApplySuggestions} 
            variant="contained" 
            disabled={loadingSuggestions || selectedSuggestions.size === 0}
          >
            Add Selected Tasks ({selectedSuggestions.size})
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};