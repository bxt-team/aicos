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
  Avatar,
  MenuItem,
  Switch,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Email as EmailIcon,
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import api from '../services/api';

interface Department {
  id: string;
  name: string;
}

interface Employee {
  id: string;
  organization_id: string;
  user_id?: string;
  department_id?: string;
  name: string;
  email: string;
  role?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  department_name?: string;
}

export const EmployeeManagement: React.FC = () => {
  const { user } = useSupabaseAuth();
  const { currentOrganization, currentUserRole } = useOrganization();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    department_id: '',
    role: '',
    is_active: true,
  });
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [employeeToDelete, setEmployeeToDelete] = useState<Employee | null>(null);
  const [filterDepartment, setFilterDepartment] = useState<string>('all');
  const [filterActive, setFilterActive] = useState<string>('all');

  useEffect(() => {
    if (currentOrganization) {
      fetchEmployees();
      fetchDepartments();
    }
  }, [currentOrganization, filterDepartment, filterActive]);

  const fetchEmployees = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    setError(null);
    try {
      let url = `/api/employees?organization_id=${currentOrganization.id}`;
      if (filterDepartment !== 'all') {
        url += `&department_id=${filterDepartment}`;
      }
      if (filterActive !== 'all') {
        url += `&is_active=${filterActive === 'active'}`;
      }
      
      const response = await api.get(url);
      setEmployees(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch employees');
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    if (!currentOrganization) return;
    
    try {
      const response = await api.get(`/api/departments?organization_id=${currentOrganization.id}`);
      setDepartments(response.data);
    } catch (err) {
      console.error('Failed to fetch departments:', err);
    }
  };

  const handleOpenDialog = (employee?: Employee) => {
    if (employee) {
      setEditingEmployee(employee);
      setFormData({
        name: employee.name,
        email: employee.email,
        department_id: employee.department_id || '',
        role: employee.role || '',
        is_active: employee.is_active,
      });
    } else {
      setEditingEmployee(null);
      setFormData({
        name: '',
        email: '',
        department_id: '',
        role: '',
        is_active: true,
      });
    }
    setFormErrors({});
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingEmployee(null);
    setFormData({
      name: '',
      email: '',
      department_id: '',
      role: '',
      is_active: true,
    });
    setFormErrors({});
  };

  const validateForm = () => {
    const errors: { [key: string]: string } = {};
    
    if (!formData.name.trim()) {
      errors.name = 'Employee name is required';
    } else if (formData.name.length > 100) {
      errors.name = 'Employee name must be less than 100 characters';
    }
    
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Invalid email address';
    }
    
    if (formData.role && formData.role.length > 100) {
      errors.role = 'Role must be less than 100 characters';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm() || !currentOrganization) return;

    const submitData: any = {
      name: formData.name,
      email: formData.email,
      role: formData.role || undefined,
      department_id: formData.department_id || undefined,
    };

    if (editingEmployee) {
      submitData.is_active = formData.is_active;
    }

    try {
      if (editingEmployee) {
        // Update existing employee
        await api.patch(
          `/api/employees/${editingEmployee.id}?organization_id=${currentOrganization.id}`,
          submitData
        );
      } else {
        // Create new employee
        await api.post(`/api/employees?organization_id=${currentOrganization.id}`, submitData);
      }
      
      handleCloseDialog();
      fetchEmployees();
    } catch (err: any) {
      setFormErrors({
        submit: err.response?.data?.detail || 'Failed to save employee',
      });
    }
  };

  const handleDeleteClick = (employee: Employee) => {
    setEmployeeToDelete(employee);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!employeeToDelete || !currentOrganization) return;

    try {
      await api.delete(
        `/api/employees/${employeeToDelete.id}?organization_id=${currentOrganization.id}`
      );
      setDeleteConfirmOpen(false);
      setEmployeeToDelete(null);
      fetchEmployees();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete employee');
      setDeleteConfirmOpen(false);
    }
  };

  const isAdmin = currentUserRole && ['admin', 'owner'].includes(currentUserRole);

  if (!currentOrganization) {
    return (
      <Box p={3}>
        <Alert severity="info">Please select an organization to manage employees.</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          <PersonIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Employees
        </Typography>
        {isAdmin && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Employee
          </Button>
        )}
      </Box>

      {/* Filters */}
      <Box mb={3} display="flex" gap={2}>
        <TextField
          select
          label="Department"
          value={filterDepartment}
          onChange={(e) => setFilterDepartment(e.target.value)}
          size="small"
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="all">All Departments</MenuItem>
          {departments.map((dept) => (
            <MenuItem key={dept.id} value={dept.id}>
              {dept.name}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Status"
          value={filterActive}
          onChange={(e) => setFilterActive(e.target.value)}
          size="small"
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="all">All</MenuItem>
          <MenuItem value="active">Active</MenuItem>
          <MenuItem value="inactive">Inactive</MenuItem>
        </TextField>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <TableContainer component={Paper}>
          <Table>
            <TableBody>
              {[1, 2, 3].map((i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton variant="circular" width={40} height={40} /></TableCell>
                  <TableCell><Skeleton variant="text" /></TableCell>
                  <TableCell><Skeleton variant="text" /></TableCell>
                  <TableCell><Skeleton variant="text" /></TableCell>
                  <TableCell><Skeleton variant="text" /></TableCell>
                  <TableCell><Skeleton variant="text" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : employees.length === 0 ? (
        <Card>
          <CardContent>
            <Typography color="textSecondary" align="center">
              No employees found. {isAdmin && 'Click "Add Employee" to get started.'}
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell></TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Department</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Status</TableCell>
                {isAdmin && <TableCell align="right">Actions</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {employees.map((employee) => (
                <TableRow key={employee.id}>
                  <TableCell>
                    <Avatar sx={{ bgcolor: 'primary.main' }}>
                      {employee.name.charAt(0).toUpperCase()}
                    </Avatar>
                  </TableCell>
                  <TableCell>{employee.name}</TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <EmailIcon sx={{ mr: 1, fontSize: 18, color: 'text.secondary' }} />
                      {employee.email}
                    </Box>
                  </TableCell>
                  <TableCell>
                    {employee.department_name || (
                      <Typography variant="body2" color="text.secondary">
                        No department
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{employee.role || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={employee.is_active ? 'Active' : 'Inactive'}
                      color={employee.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  {isAdmin && (
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(employee)}
                        title="Edit employee"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteClick(employee)}
                        title="Delete employee"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingEmployee ? 'Edit Employee' : 'Add New Employee'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Full Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              error={!!formErrors.name}
              helperText={formErrors.name}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              error={!!formErrors.email}
              helperText={formErrors.email}
              margin="normal"
              required
              disabled={!!editingEmployee}
            />
            <TextField
              fullWidth
              select
              label="Department"
              value={formData.department_id}
              onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
              margin="normal"
            >
              <MenuItem value="">No Department</MenuItem>
              {departments.map((dept) => (
                <MenuItem key={dept.id} value={dept.id}>
                  {dept.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              fullWidth
              label="Role/Title"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              error={!!formErrors.role}
              helperText={formErrors.role}
              margin="normal"
              placeholder="e.g., Software Engineer, Manager"
            />
            {editingEmployee && (
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                }
                label="Active"
                sx={{ mt: 2 }}
              />
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
            {editingEmployee ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the employee "{employeeToDelete?.name}"?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone. The employee will be permanently removed.
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