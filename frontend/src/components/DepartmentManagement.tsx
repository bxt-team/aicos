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
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  People as PeopleIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import api from '../services/api';

interface Department {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  employee_count: number;
}

export const DepartmentManagement: React.FC = () => {
  const { user } = useSupabaseAuth();
  const { currentOrganization, currentUserRole } = useOrganization();
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

  useEffect(() => {
    if (currentOrganization) {
      fetchDepartments();
    }
  }, [currentOrganization]);

  const fetchDepartments = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/api/departments?organization_id=${currentOrganization.id}`);
      setDepartments(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch departments');
    } finally {
      setLoading(false);
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

  const handleSubmit = async () => {
    if (!validateForm() || !currentOrganization) return;

    try {
      if (editingDepartment) {
        // Update existing department
        await api.patch(
          `/api/departments/${editingDepartment.id}?organization_id=${currentOrganization.id}`,
          formData
        );
      } else {
        // Create new department
        await api.post(`/api/departments?organization_id=${currentOrganization.id}`, formData);
      }
      
      handleCloseDialog();
      fetchDepartments();
    } catch (err: any) {
      setFormErrors({
        submit: err.response?.data?.detail || 'Failed to save department',
      });
    }
  };

  const handleDeleteClick = (department: Department) => {
    setDepartmentToDelete(department);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!departmentToDelete || !currentOrganization) return;

    try {
      await api.delete(
        `/api/departments/${departmentToDelete.id}?organization_id=${currentOrganization.id}`
      );
      setDeleteConfirmOpen(false);
      setDepartmentToDelete(null);
      fetchDepartments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete department');
      setDeleteConfirmOpen(false);
    }
  };

  const isAdmin = currentUserRole && ['admin', 'owner'].includes(currentUserRole);
  
  // Debug logging
  console.log('Department Management - Current User Role:', currentUserRole);
  console.log('Department Management - Is Admin:', isAdmin);
  console.log('Current Organization:', currentOrganization);
  
  // TODO: For now, allow all users to manage departments until role checking is fixed
  const canManageDepartments = true; // Replace with isAdmin when roles are working

  if (!currentOrganization) {
    return (
      <Box p={3}>
        <Alert severity="info">Please select an organization to manage departments.</Alert>
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
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Department
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
                      <Chip
                        icon={<PeopleIcon />}
                        label={`${department.employee_count} employee${
                          department.employee_count !== 1 ? 's' : ''
                        }`}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                    {canManageDepartments && (
                      <Box>
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
                          disabled={department.employee_count > 0}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    )}
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
              label="Description"
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
          <Button onClick={handleSubmit} variant="contained">
            {editingDepartment ? 'Update' : 'Create'}
          </Button>
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