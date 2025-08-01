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
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  TextField,
  Typography,
  Alert,
  Chip,
  Skeleton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Avatar,
  Stack,
  Divider,
  Tab,
  Tabs,
  CircularProgress,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  People as PeopleIcon,
  Business as BusinessIcon,
  SmartToy as SmartToyIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { useProject } from '../contexts/ProjectContext';
import api from '../services/api';
import { useTranslation } from 'react-i18next';

interface Department {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  member_count: number;
  ai_agent_count: number;
}

interface DepartmentAssignment {
  id: string;
  department_id: string;
  assignee_type: 'member' | 'ai_agent';
  assignee_id: string;
  assignee_name: string;
  assignee_metadata: any;
  role?: string;
  assigned_at: string;
  assigned_by?: string;
  member_email?: string;
  member_full_name?: string;
}

interface AIAgent {
  id: string;
  name: string;
  type: string;
  capabilities: string[];
}

interface OrganizationMember {
  id: string;
  user_id: string;
  role: string;
  email: string;
  full_name?: string;
}

interface PredefinedDepartment {
  emoji: string;
  name: string;
  goal: string;
  aiAgents: string[];
}

const PREDEFINED_DEPARTMENTS: PredefinedDepartment[] = [
  {
    emoji: '🧠',
    name: 'Growth & Marketing Department',
    goal: 'Automate customer acquisition, branding, and engagement.',
    aiAgents: [
      'Content Generation Agent (reels, blogs, newsletters)',
      'Campaign Testing Agent (A/B testing ads)',
      'Scheduler & Posting Agent',
      'SEO & Keyword Optimizer Agent'
    ]
  },
  {
    emoji: '🛍️',
    name: 'Sales & Lead Management',
    goal: 'Automate lead nurturing, sales funnels, and conversion.',
    aiAgents: [
      'Lead Scoring Agent',
      'CRM Update Agent',
      'Follow-up Email Agent',
      'Proposal Generator Agent'
    ]
  },
  {
    emoji: '💬',
    name: 'Customer Support & Success',
    goal: 'Ensure satisfaction, solve problems, and retain users.',
    aiAgents: [
      'Chatbot Agent (contextual support)',
      'Ticket Categorization Agent',
      'Sentiment Analyzer Agent',
      'Onboarding Flow Agent'
    ]
  },
  {
    emoji: '🧾',
    name: 'Finance & Accounting',
    goal: 'Automate transactions, billing, cash flow tracking.',
    aiAgents: [
      'Invoice Parser Agent',
      'Subscription Tracking Agent',
      'Expense Categorizer Agent',
      'Forecasting Agent (MRR/ARR)'
    ]
  },
  {
    emoji: '👨‍💻',
    name: 'Product & Development',
    goal: 'AI-assisted feature development, testing & documentation.',
    aiAgents: [
      'Roadmap Prioritizer Agent',
      'Code Explainer Agent',
      'UI Tester Agent',
      'Documentation Agent'
    ]
  },
  {
    emoji: '📦',
    name: 'Operations & Logistics',
    goal: 'Manage workflows, delivery pipelines, team syncs.',
    aiAgents: [
      'Task Sync Agent (Notion/Jira)',
      'Resource Optimizer Agent',
      'Delivery Tracker Agent',
      'SOP Generator Agent'
    ]
  },
  {
    emoji: '📚',
    name: 'Content & Knowledge Management',
    goal: 'Create, reuse, and manage all internal/external knowledge.',
    aiAgents: [
      'Blog & Social Post Generator',
      'Internal Wiki Agent',
      'Video Transcript + Summary Agent',
      'Searchable Docs Agent'
    ]
  },
  {
    emoji: '🧑‍💼',
    name: 'HR & Recruiting',
    goal: 'Simplify hiring, onboarding, and internal feedback.',
    aiAgents: [
      'CV Screening Agent',
      'Interview Question Generator',
      'Onboarding Task Generator',
      'Team Feedback Analyzer'
    ]
  },
  {
    emoji: '🧑‍⚖️',
    name: 'Legal & Compliance',
    goal: 'Automate risk checks, contracts, and regulatory workflows.',
    aiAgents: [
      'Contract Checker Agent',
      'GDPR Checker Agent',
      'Terms & Policy Generator',
      'Risk Alerting Agent'
    ]
  },
  {
    emoji: '📈',
    name: 'Analytics & Strategy',
    goal: 'Turn raw data into business decisions & reports.',
    aiAgents: [
      'Dashboard Agent',
      'Goal Progress Analyzer',
      'User Cohort Insights Agent',
      'Strategic Idea Recommender'
    ]
  }
];

export const DepartmentManagement: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useSupabaseAuth();
  const { currentOrganization, currentUserRole } = useOrganization();
  const { currentProject } = useProject();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [departmentToDelete, setDepartmentToDelete] = useState<Department | null>(null);
  
  // Assignment management
  const [assignmentDialog, setAssignmentDialog] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null);
  const [assignments, setAssignments] = useState<DepartmentAssignment[]>([]);
  const [availableAgents, setAvailableAgents] = useState<AIAgent[]>([]);
  const [organizationMembers, setOrganizationMembers] = useState<OrganizationMember[]>([]);
  const [assignmentType, setAssignmentType] = useState<'member' | 'ai_agent'>('member');
  const [selectedAssignee, setSelectedAssignee] = useState('');
  const [assignmentRole, setAssignmentRole] = useState('');
  const [assignmentTab, setAssignmentTab] = useState(0);
  
  // Predefined department selection state
  const [selectedPredefinedDept, setSelectedPredefinedDept] = useState<number>(-1);
  const [showPredefinedList, setShowPredefinedList] = useState(false);

  useEffect(() => {
    if (currentProject) {
      fetchDepartments();
      fetchAvailableAgents();
      fetchOrganizationMembers();
    }
  }, [currentProject]);

  const fetchDepartments = async () => {
    if (!currentProject) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/api/departments?project_id=${currentProject.id}`);
      setDepartments(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToFetch', { resource: t('department.departments').toLowerCase() }));
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableAgents = async () => {
    try {
      const response = await api.get('/api/departments/ai-agents');
      setAvailableAgents(response.data);
    } catch (err) {
      console.error('Failed to fetch AI agents:', err);
    }
  };

  const fetchOrganizationMembers = async () => {
    if (!currentOrganization) return;
    
    try {
      const response = await api.get(`/api/organizations/${currentOrganization.id}/members`);
      setOrganizationMembers(response.data);
    } catch (err) {
      console.error('Failed to fetch organization members:', err);
    }
  };

  const fetchAssignments = async (departmentId: string) => {
    try {
      const response = await api.get(`/api/departments/${departmentId}/assignments`);
      setAssignments(response.data);
    } catch (err) {
      console.error('Failed to fetch assignments:', err);
    }
  };

  const handleOpenDialog = (department?: Department) => {
    if (department) {
      setEditingDepartment(department);
      setFormData({
        name: department.name,
        description: department.description || '',
      });
    } else {
      setEditingDepartment(null);
      setFormData({
        name: '',
        description: '',
      });
    }
    setFormErrors({});
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingDepartment(null);
    setFormData({
      name: '',
      description: '',
    });
    setFormErrors({});
    setShowPredefinedList(false);
    setSelectedPredefinedDept(-1);
  };

  const validateForm = () => {
    const errors: { [key: string]: string } = {};
    
    if (!formData.name.trim()) {
      errors.name = 'Department name is required';
    } else if (formData.name.length > 100) {
      errors.name = 'Department name must be less than 100 characters';
    }
    
    if (formData.description && formData.description.length > 500) {
      errors.description = 'Description must be less than 500 characters';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (department?: Department | null, data?: { name: string; description: string }) => {
    const dataToSubmit = data || formData;
    const isEdit = department || editingDepartment;
    
    if (!data && (!validateForm() || !currentProject)) return;
    if (!currentProject) return;

    try {
      if (isEdit) {
        // Update existing department
        await api.patch(
          `/api/departments/${isEdit.id}`,
          dataToSubmit
        );
      } else {
        // Create new department
        await api.post(`/api/departments?project_id=${currentProject.id}`, dataToSubmit);
      }
      
      if (!data) {
        handleCloseDialog();
      }
      fetchDepartments();
    } catch (err: any) {
      if (!data) {
        setFormErrors({
          submit: err.response?.data?.detail || 'Failed to save department',
        });
      } else {
        throw err;
      }
    }
  };

  const handleDeleteClick = (department: Department) => {
    setDepartmentToDelete(department);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!departmentToDelete) return;

    try {
      await api.delete(`/api/departments/${departmentToDelete.id}`);
      setDeleteConfirmOpen(false);
      setDepartmentToDelete(null);
      fetchDepartments();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToDelete', { resource: t('department.department').toLowerCase() }));
      setDeleteConfirmOpen(false);
    }
  };

  const handleOpenAssignments = async (department: Department) => {
    setSelectedDepartment(department);
    setAssignmentDialog(true);
    setAssignmentTab(0);
    await fetchAssignments(department.id);
  };

  const handleAssignmentSubmit = async () => {
    if (!selectedDepartment || !selectedAssignee) return;

    try {
      await api.post(`/api/departments/${selectedDepartment.id}/assignments`, {
        assignee_type: assignmentType,
        assignee_id: selectedAssignee,
        role: assignmentRole || null,
      });
      
      // Refresh assignments and departments
      await fetchAssignments(selectedDepartment.id);
      await fetchDepartments();
      
      // Reset form
      setSelectedAssignee('');
      setAssignmentRole('');
      setAssignmentType('member');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToCreate', { resource: t('common.assignment', 'assignment') }));
    }
  };

  const handleRemoveAssignment = async (assignmentId: string) => {
    if (!selectedDepartment) return;

    try {
      await api.delete(`/api/departments/${selectedDepartment.id}/assignments/${assignmentId}`);
      await fetchAssignments(selectedDepartment.id);
      await fetchDepartments();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.failedToDelete', { resource: t('common.assignment', 'assignment') }));
    }
  };

  const isAdmin = currentUserRole && ['admin', 'owner'].includes(currentUserRole);
  const canManageDepartments = isAdmin;

  if (!currentProject) {
    return (
      <Box p={3}>
        <Alert severity="info">Please select a project to manage departments.</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          <BusinessIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          {t('department.departments')}
        </Typography>
        {canManageDepartments && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            {t('department.addDepartment', 'Add Department')}
          </Button>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Grid container spacing={2}>
          {[1, 2, 3].map((i) => (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={i}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" width="60%" height={32} />
                  <Skeleton variant="text" width="100%" />
                  <Skeleton variant="text" width="40%" />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : departments.length === 0 ? (
        <Card>
          <CardContent>
            <Typography color="textSecondary" align="center">
              No departments created yet. {canManageDepartments && 'Click "Add Department" to get started.'}
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {departments.map((department) => (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={department.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                    <Box flex={1}>
                      <Typography variant="h6" gutterBottom>
                        {department.name}
                      </Typography>
                      {department.description && (
                        <Typography
                          variant="body2"
                          color="textSecondary"
                          sx={{ mb: 2 }}
                        >
                          {department.description}
                        </Typography>
                      )}
                      <Stack direction="row" spacing={1}>
                        <Chip
                          icon={<PersonIcon />}
                          label={`${department.member_count} member${
                            department.member_count !== 1 ? 's' : ''
                          }`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          icon={<SmartToyIcon />}
                          label={`${department.ai_agent_count} AI agent${
                            department.ai_agent_count !== 1 ? 's' : ''
                          }`}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      </Stack>
                    </Box>
                    <Box>
                      <Button
                        size="small"
                        onClick={() => handleOpenAssignments(department)}
                        startIcon={<PeopleIcon />}
                      >
                        Manage
                      </Button>
                      {canManageDepartments && (
                        <>
                          <IconButton
                            size="small"
                            onClick={() => handleOpenDialog(department)}
                            title="Edit department"
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteClick(department)}
                            title="Delete department"
                            disabled={department.member_count > 0 || department.ai_agent_count > 0}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </>
                      )}
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingDepartment ? 'Edit Department' : 'Create New Department'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {!editingDepartment && !showPredefinedList && (
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Choose how to create your department:
                </Typography>
                <Stack direction="row" spacing={2} mt={2}>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={() => setShowPredefinedList(true)}
                    startIcon={<BusinessIcon />}
                  >
                    Select from Templates
                  </Button>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={() => {
                      setShowPredefinedList(false);
                      setSelectedPredefinedDept(-1);
                    }}
                    startIcon={<EditIcon />}
                  >
                    Create Custom
                  </Button>
                </Stack>
              </Box>
            )}
            
            {!editingDepartment && showPredefinedList && (
              <Box>
                <Button
                  size="small"
                  onClick={() => {
                    setShowPredefinedList(false);
                    setSelectedPredefinedDept(-1);
                    setFormData({ name: '', description: '' });
                  }}
                  sx={{ mb: 2 }}
                >
                  ← Back to options
                </Button>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Select a department template:
                </Typography>
                <Grid container spacing={2} sx={{ mt: 1, mb: 2, maxHeight: 400, overflow: 'auto' }}>
                  {PREDEFINED_DEPARTMENTS.map((dept, index) => (
                    <Grid size={{ xs: 12 }} key={index}>
                      <Card
                        variant={selectedPredefinedDept === index ? "elevation" : "outlined"}
                        sx={{
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          bgcolor: selectedPredefinedDept === index ? 'action.selected' : 'background.paper'
                        }}
                        onClick={() => {
                          setSelectedPredefinedDept(index);
                          const selected = PREDEFINED_DEPARTMENTS[index];
                          setFormData({
                            name: `${selected.emoji} ${selected.name}`,
                            description: `Goal: ${selected.goal}\n\nAI-Agents Examples:\n${selected.aiAgents.map(agent => `• ${agent}`).join('\n')}`
                          });
                        }}
                      >
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            {dept.emoji} {dept.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" paragraph>
                            {dept.goal}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}
            
            {(editingDepartment || !showPredefinedList || selectedPredefinedDept >= 0) && (
              <>
                <TextField
                  fullWidth
                  label="Department Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  error={!!formErrors.name}
                  helperText={formErrors.name}
                  margin="normal"
                  required
                />
                <TextField
                  fullWidth
                  label="Goals & Description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  error={!!formErrors.description}
                  helperText={formErrors.description}
                  margin="normal"
                  multiline
                  rows={6}
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
          <Button onClick={() => {
            handleCloseDialog();
            setShowPredefinedList(false);
            setSelectedPredefinedDept(-1);
          }}>Cancel</Button>
          <Button 
            onClick={() => handleSubmit()} 
            variant="contained"
            disabled={showPredefinedList && selectedPredefinedDept < 0 && !editingDepartment}
          >
            {editingDepartment ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Assignment Management Dialog */}
      <Dialog 
        open={assignmentDialog} 
        onClose={() => setAssignmentDialog(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          {selectedDepartment?.name} - Assignments
        </DialogTitle>
        <DialogContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={assignmentTab} onChange={(e, v) => setAssignmentTab(v)}>
              <Tab label="Current Assignments" />
              <Tab label="Add New Assignment" disabled={!canManageDepartments} />
            </Tabs>
          </Box>

          {assignmentTab === 0 && (
            <Box sx={{ mt: 2 }}>
              {assignments.length === 0 ? (
                <Typography color="textSecondary" align="center" sx={{ py: 3 }}>
                  No assignments yet
                </Typography>
              ) : (
                <List>
                  {assignments.map((assignment) => (
                    <ListItem key={assignment.id}>
                      <Avatar sx={{ mr: 2 }}>
                        {assignment.assignee_type === 'ai_agent' ? (
                          <SmartToyIcon />
                        ) : (
                          <PersonIcon />
                        )}
                      </Avatar>
                      <ListItemText
                        primary={assignment.assignee_name}
                        secondary={
                          <>
                            {assignment.assignee_type === 'ai_agent' ? 'AI Agent' : 'Member'}
                            {assignment.role && ` • ${assignment.role}`}
                            {assignment.member_email && ` • ${assignment.member_email}`}
                          </>
                        }
                      />
                      {canManageDepartments && (
                        <ListItemSecondaryAction>
                          <IconButton
                            edge="end"
                            onClick={() => handleRemoveAssignment(assignment.id)}
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
          )}

          {assignmentTab === 1 && canManageDepartments && (
            <Box sx={{ mt: 2 }}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Assignment Type</InputLabel>
                <Select
                  value={assignmentType}
                  onChange={(e: SelectChangeEvent) => {
                    setAssignmentType(e.target.value as 'member' | 'ai_agent');
                    setSelectedAssignee('');
                  }}
                  label="Assignment Type"
                >
                  <MenuItem value="member">Organization Member</MenuItem>
                  <MenuItem value="ai_agent">AI Agent</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>
                  {assignmentType === 'member' ? 'Select Member' : 'Select AI Agent'}
                </InputLabel>
                <Select
                  value={selectedAssignee}
                  onChange={(e: SelectChangeEvent) => setSelectedAssignee(e.target.value)}
                  label={assignmentType === 'member' ? 'Select Member' : 'Select AI Agent'}
                >
                  {assignmentType === 'member' ? (
                    organizationMembers
                      .filter(member => !assignments.some(a => 
                        a.assignee_type === 'member' && a.assignee_id === member.user_id
                      ))
                      .map((member) => (
                        <MenuItem key={member.user_id} value={member.user_id}>
                          {member.full_name || member.email} ({member.role})
                        </MenuItem>
                      ))
                  ) : (
                    availableAgents
                      .filter(agent => !assignments.some(a => 
                        a.assignee_type === 'ai_agent' && 
                        a.assignee_metadata?.agent_id === agent.id
                      ))
                      .map((agent) => (
                        <MenuItem key={agent.id} value={agent.id}>
                          {agent.name}
                        </MenuItem>
                      ))
                  )}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Role (optional)"
                value={assignmentRole}
                onChange={(e) => setAssignmentRole(e.target.value)}
                sx={{ mb: 2 }}
                helperText="e.g., Team Lead, Specialist, etc."
              />

              <Button
                variant="contained"
                fullWidth
                onClick={handleAssignmentSubmit}
                disabled={!selectedAssignee}
              >
                Add Assignment
              </Button>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssignmentDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the department "{departmentToDelete?.name}"?
          </Typography>
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