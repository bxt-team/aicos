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
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  People as PeopleIcon,
  Business as BusinessIcon,
  SmartToy as SmartToyIcon,
  Person as PersonIcon,
  AutoAwesome as AIIcon,
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { useProject } from '../contexts/ProjectContext';
import api from '../services/api';
import { organizationManagementService, DepartmentSuggestion } from '../services/organizationManagementService';

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

export const DepartmentManagement: React.FC = () => {
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
  
  // AI Suggestion state
  const [aiSuggestDialogOpen, setAISuggestDialogOpen] = useState(false);
  const [aiLoading, setAILoading] = useState(false);
  const [aiError, setAIError] = useState<string | null>(null);
  const [aiSuggestions, setAISuggestions] = useState<DepartmentSuggestion[] | null>(null);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(new Set());
  const [aiUserFeedback, setAIUserFeedback] = useState('');
  const [aiCompanySize, setAICompanySize] = useState('small');
  const [aiIndustry, setAIIndustry] = useState('');

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
      setError(err.response?.data?.detail || 'Failed to fetch departments');
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
      setError(err.response?.data?.detail || 'Failed to delete department');
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
      setError(err.response?.data?.detail || 'Failed to create assignment');
    }
  };

  const handleRemoveAssignment = async (assignmentId: string) => {
    if (!selectedDepartment) return;

    try {
      await api.delete(`/api/departments/${selectedDepartment.id}/assignments/${assignmentId}`);
      await fetchAssignments(selectedDepartment.id);
      await fetchDepartments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove assignment');
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
          Departments
        </Typography>
        {canManageDepartments && (
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              startIcon={<AIIcon />}
              onClick={() => setAISuggestDialogOpen(true)}
            >
              AI Suggest Departments
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
            >
              Add Department
            </Button>
          </Box>
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
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingDepartment ? 'Edit Department' : 'Create New Department'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
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
              rows={3}
            />
            {formErrors.submit && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {formErrors.submit}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={() => handleSubmit()} variant="contained">
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

      {/* AI Department Suggestion Dialog */}
      <Dialog 
        open={aiSuggestDialogOpen} 
        onClose={() => {
          setAISuggestDialogOpen(false);
          setAISuggestions(null);
          setSelectedSuggestions(new Set());
          setAIUserFeedback('');
          setAIError(null);
        }}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <AIIcon color="primary" />
            <Typography variant="h6">AI Department Structure Suggestions</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {aiError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {aiError}
            </Alert>
          )}
          
          {!aiSuggestions ? (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Our AI will analyze your organization and suggest an optimal department structure
                based on your goals, industry, and company size.
              </Typography>
              
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Company Size</InputLabel>
                    <Select
                      value={aiCompanySize}
                      onChange={(e) => setAICompanySize(e.target.value)}
                      label="Company Size"
                    >
                      <MenuItem value="small">Small (1-10 employees)</MenuItem>
                      <MenuItem value="medium">Medium (11-50 employees)</MenuItem>
                      <MenuItem value="large">Large (51-200 employees)</MenuItem>
                      <MenuItem value="enterprise">Enterprise (200+ employees)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Industry (optional)"
                    placeholder="e.g., Software, Healthcare, Retail"
                    value={aiIndustry}
                    onChange={(e) => setAIIndustry(e.target.value)}
                    margin="normal"
                  />
                </Grid>
              </Grid>
              
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Additional Context (optional)"
                placeholder="Any specific requirements or focus areas for your departments?"
                value={aiUserFeedback}
                onChange={(e) => setAIUserFeedback(e.target.value)}
                margin="normal"
              />
            </Box>
          ) : (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Select the departments you'd like to create:
              </Typography>
              
              <Grid container spacing={2}>
                {aiSuggestions.map((dept, index) => (
                  <Grid size={{ xs: 12, md: 6 }} key={index}>
                    <Card 
                      variant={selectedSuggestions.has(index) ? "elevation" : "outlined"}
                      sx={{ 
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        bgcolor: selectedSuggestions.has(index) ? 'action.selected' : 'background.paper'
                      }}
                      onClick={() => {
                        const newSelected = new Set(selectedSuggestions);
                        if (newSelected.has(index)) {
                          newSelected.delete(index);
                        } else {
                          newSelected.add(index);
                        }
                        setSelectedSuggestions(newSelected);
                      }}
                    >
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {dept.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {dept.description}
                        </Typography>
                        <Typography variant="subtitle2" gutterBottom>
                          Key Goals:
                        </Typography>
                        <Box component="ul" sx={{ pl: 2, mt: 0 }}>
                          {dept.goals.slice(0, 3).map((goal, i) => (
                            <Typography component="li" variant="body2" key={i}>
                              {goal}
                            </Typography>
                          ))}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              
              <Divider sx={{ my: 3 }} />
              
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Feedback for refinement (optional)"
                placeholder="What would you like to adjust about these suggestions?"
                value={aiUserFeedback}
                onChange={(e) => setAIUserFeedback(e.target.value)}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setAISuggestDialogOpen(false);
            setAISuggestions(null);
            setSelectedSuggestions(new Set());
            setAIUserFeedback('');
            setAIError(null);
          }}>
            Cancel
          </Button>
          {!aiSuggestions ? (
            <Button
              onClick={async () => {
                if (!currentOrganization) return;
                
                setAILoading(true);
                setAIError(null);
                try {
                  const result = await organizationManagementService.suggestDepartments({
                    organization_description: currentOrganization.description || currentOrganization.name,
                    organization_goals: [], // TODO: Add primary_goals to Organization interface when AI-enhanced goals are saved
                    industry: aiIndustry || undefined,
                    company_size: aiCompanySize,
                    user_feedback: aiUserFeedback || undefined
                  });
                  setAISuggestions(result.departments);
                  setSelectedSuggestions(new Set(result.departments.map((_, i) => i)));
                } catch (error: any) {
                  setAIError(error.response?.data?.detail || 'Failed to generate suggestions');
                } finally {
                  setAILoading(false);
                }
              }}
              variant="contained"
              disabled={aiLoading}
              startIcon={aiLoading ? <CircularProgress size={20} /> : <AIIcon />}
            >
              {aiLoading ? 'Generating...' : 'Generate Suggestions'}
            </Button>
          ) : (
            <>
              <Button
                onClick={async () => {
                  setAISuggestions(null);
                  setSelectedSuggestions(new Set());
                }}
                disabled={aiLoading}
              >
                Regenerate
              </Button>
              <Button
                onClick={async () => {
                  // Create the selected departments
                  const selectedDepts = Array.from(selectedSuggestions).map(i => aiSuggestions[i]);
                  
                  setAILoading(true);
                  try {
                    for (const dept of selectedDepts) {
                      await handleSubmit(null, {
                        name: dept.name,
                        description: `${dept.description}\n\nGoals:\n${dept.goals.join('\n')}\n\nKey Responsibilities:\n${dept.key_responsibilities.join('\n')}`
                      });
                    }
                    
                    await fetchDepartments();
                    setAISuggestDialogOpen(false);
                    setAISuggestions(null);
                    setSelectedSuggestions(new Set());
                    setError(null);
                  } catch (error: any) {
                    setAIError('Failed to create some departments');
                  } finally {
                    setAILoading(false);
                  }
                }}
                variant="contained"
                color="primary"
                disabled={selectedSuggestions.size === 0 || aiLoading}
              >
                Create {selectedSuggestions.size} Department{selectedSuggestions.size !== 1 ? 's' : ''}
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};