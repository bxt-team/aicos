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
  Grid,
  Checkbox,
  Rating,
  Paper,
  CircularProgress,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Flag as FlagIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Assignment as AssignmentIcon,
  AutoAwesome as AutoAwesomeIcon,
  Feedback as FeedbackIcon,
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
  const { } = useSupabaseAuth();
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
  const [suggestDialogOpen, setSuggestDialogOpen] = useState(false);
  const [suggestedGoals, setSuggestedGoals] = useState<any[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(new Set());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [goalRatings, setGoalRatings] = useState<{ [key: number]: number }>({});
  const [goalFeedback, setGoalFeedback] = useState<{ [key: number]: string }>({});
  const [feedbackSummary, setFeedbackSummary] = useState<any>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [promptTemplateOpen, setPromptTemplateOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(0);
  const [customPrompt, setCustomPrompt] = useState('');

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

  const promptTemplates = [
    {
      name: 'Strategic Business Goals',
      description: 'Generate high-level strategic goals for business growth and development',
      prompt: 'Generate strategic business goals that focus on growth, market expansion, and competitive advantage. Consider revenue targets, market positioning, and long-term sustainability.',
    },
    {
      name: 'Operational Excellence',
      description: 'Create goals focused on improving operational efficiency and processes',
      prompt: 'Generate operational goals that improve efficiency, reduce costs, and enhance quality. Focus on process optimization, automation opportunities, and performance metrics.',
    },
    {
      name: 'Innovation & Development',
      description: 'Develop goals for innovation, R&D, and product/service development',
      prompt: 'Generate innovation-focused goals for new product development, research initiatives, and technological advancement. Include experimentation, prototyping, and market validation.',
    },
  ];

  const handleOpenPromptDialog = () => {
    setCustomPrompt(promptTemplates[selectedTemplate].prompt);
    setPromptTemplateOpen(true);
  };

  const handleSuggestGoals = async () => {
    if (!projectId) {
      setError('Please select a project first');
      return;
    }

    setPromptTemplateOpen(false);
    setLoadingSuggestions(true);
    setSuggestDialogOpen(true);
    setError(null);
    setShowFeedbackForm(false);
    setGoalRatings({});
    setGoalFeedback({});

    try {
      // First fetch feedback summary
      try {
        const summaryResponse = await api.get(`/api/goals/feedback/summary?project_id=${projectId}`);
        setFeedbackSummary(summaryResponse.data);
      } catch (err) {
        // Continue without feedback summary
      }

      const response = await api.post('/api/goals/suggest', {
        project_id: projectId,
        include_knowledge_base: true,
        session_id: sessionId,
        custom_prompt: customPrompt,
      });

      setSuggestedGoals(response.data.goals || []);
      setSessionId(response.data.session_id || null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate goal suggestions');
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
    if (!sessionId || !projectId) return;

    try {
      const feedbackData = suggestedGoals.map((goal, index) => ({
        goal_index: index,
        feedback_type: selectedSuggestions.has(index) ? 'accepted' : 'rejected',
        rating: goalRatings[index] || undefined,
        feedback_text: goalFeedback[index] || undefined,
      }));

      await api.post('/api/goals/suggest/feedback', {
        project_id: projectId,
        session_id: sessionId,
        suggested_goals: suggestedGoals,
        feedback: feedbackData,
      });

      setShowFeedbackForm(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    }
  };

  const handleApplySuggestions = async () => {
    const goalsToCreate = Array.from(selectedSuggestions).map(index => suggestedGoals[index]);
    
    // Submit feedback before creating goals
    if (showFeedbackForm) {
      await handleSubmitFeedback();
    }
    
    for (const goal of goalsToCreate) {
      try {
        await api.post('/api/goals', {
          project_id: projectId,
          title: goal.title,
          description: `${goal.description}\n\nSuccess Criteria:\n${goal.success_criteria.map((c: string, i: number) => `${i + 1}. ${c}`).join('\n')}\n\nKey Milestones:\n${goal.key_milestones.map((m: string, i: number) => `${i + 1}. ${m}`).join('\n')}`,
          // Parse target date suggestion (e.g., "3 months" -> actual date)
          target_date: goal.target_date_suggestion ? calculateTargetDate(goal.target_date_suggestion) : null,
        });
      } catch (err: any) {
        setError(`Failed to create goal "${goal.title}": ${err.response?.data?.detail || err.message}`);
      }
    }

    setSuggestDialogOpen(false);
    setSuggestedGoals([]);
    setSelectedSuggestions(new Set());
    setSessionId(null);
    fetchGoals();
  };

  const calculateTargetDate = (suggestion: string): string | null => {
    const now = new Date();
    const match = suggestion.match(/(\d+)\s*(week|month|day|year)/i);
    
    if (!match) return null;
    
    const [, amount, unit] = match;
    const num = parseInt(amount);
    
    switch (unit.toLowerCase()) {
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
      case 'year':
      case 'years':
        now.setFullYear(now.getFullYear() + num);
        break;
    }
    
    return now.toISOString().split('T')[0];
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
        <Box display="flex" gap={1}>
          {projectId && (
            <Button
              variant="outlined"
              startIcon={<AutoAwesomeIcon />}
              onClick={handleOpenPromptDialog}
              color="primary"
            >
              AI Suggest
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            disabled={!projectId && projects.length === 0}
          >
            Add Goal
          </Button>
        </Box>
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
              {projectId 
                ? 'No goals created yet. Click "Add Goal" to get started.'
                : projects.length === 0
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
            Choose AI Goal Generation Template
          </Box>
        </DialogTitle>
        <DialogContent>
          <FormControl component="fieldset" sx={{ width: '100%' }}>
            <FormLabel component="legend" sx={{ mb: 2 }}>
              Select a template or customize the prompt for your specific needs:
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
              placeholder="Enter your custom prompt for goal generation..."
              helperText="You can modify the prompt to better suit your specific needs and context"
              sx={{ mt: 1 }}
            />
          </Box>
          
          <Alert severity="info" sx={{ mt: 2 }}>
            The AI will use this prompt along with your project context and knowledge base to generate relevant goals.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPromptTemplateOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSuggestGoals}
            variant="contained"
            startIcon={<AutoAwesomeIcon />}
            disabled={!customPrompt.trim()}
          >
            Generate Goals
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
            AI Goal Suggestions
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
                    Analyzing your project context and knowledge base
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
                
                {/* Progress steps */}
                <Box sx={{ width: '100%', maxWidth: 400 }}>
                  <LinearProgress
                    variant="indeterminate"
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 3,
                        background: 'linear-gradient(90deg, #1976d2 0%, #42a5f5 50%, #1976d2 100%)',
                        backgroundSize: '200% 100%',
                        animation: 'shimmer 2s linear infinite',
                      },
                      '@keyframes shimmer': {
                        '0%': {
                          backgroundPosition: '200% 0',
                        },
                        '100%': {
                          backgroundPosition: '-200% 0',
                        },
                      },
                    }}
                  />
                  <Box display="flex" justifyContent="space-between" mt={1}>
                    <Typography variant="caption" color="textSecondary">
                      Analyzing context
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Generating suggestions
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Box>
          ) : suggestedGoals.length > 0 ? (
            <>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Select the goals you'd like to add to your project:
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
                {suggestedGoals.map((goal, index) => (
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
                            {goal.title}
                          </Typography>
                          <Typography variant="body2" paragraph>
                            {goal.description}
                          </Typography>
                          <Box display="flex" gap={1} mb={1}>
                            <Chip 
                              label={goal.priority} 
                              size="small" 
                              color={goal.priority === 'urgent' ? 'error' : goal.priority === 'high' ? 'warning' : 'default'}
                            />
                            <Chip 
                              label={`Target: ${goal.target_date_suggestion}`} 
                              size="small" 
                              variant="outlined"
                            />
                          </Box>
                          <Typography variant="caption" color="textSecondary">
                            <strong>Rationale:</strong> {goal.rationale}
                          </Typography>
                          
                          {/* Feedback Form */}
                          {showFeedbackForm && (
                            <Box mt={2} p={2} bgcolor="background.default" borderRadius={1}>
                              <Typography variant="subtitle2" gutterBottom>
                                Rate this suggestion:
                              </Typography>
                              <Rating
                                value={goalRatings[index] || 0}
                                onChange={(event, newValue) => {
                                  setGoalRatings({ ...goalRatings, [index]: newValue || 0 });
                                }}
                                size="small"
                              />
                              <TextField
                                fullWidth
                                size="small"
                                placeholder="Optional feedback..."
                                value={goalFeedback[index] || ''}
                                onChange={(e) => {
                                  setGoalFeedback({ ...goalFeedback, [index]: e.target.value });
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
            Add Selected Goals ({selectedSuggestions.size})
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};