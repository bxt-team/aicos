import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
  Folder as FolderIcon,
  AutoAwesome as AIIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useOrganization } from '../../contexts/OrganizationContext';
import { apiService } from '../../services/api';

interface OrganizationProjectsProps {
  organizationId: string;
}

export const OrganizationProjects: React.FC<OrganizationProjectsProps> = ({ organizationId }) => {
  const navigate = useNavigate();
  const { currentOrganization, currentUserRole } = useOrganization();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [projects, setProjects] = useState<any[]>([]);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');

  useEffect(() => {
    if (organizationId) {
      loadProjects();
    }
  }, [organizationId]);

  const loadProjects = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await apiService.projects.list(organizationId);
      setProjects(response.data.projects || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading projects');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiService.projects.create({
        name: newProjectName,
        description: newProjectDescription,
        organization_id: organizationId
      });
      
      setSuccess('Project successfully created');
      setCreateDialogOpen(false);
      setNewProjectName('');
      setNewProjectDescription('');
      loadProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error creating project');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async (projectId: string, projectName: string) => {
    if (!window.confirm(`Are you sure you want to delete "${projectName}"? This action cannot be undone.`)) return;
    
    try {
      await apiService.projects.delete(projectId);
      setSuccess('Project successfully deleted');
      loadProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error deleting project');
    }
  };

  const handleViewProject = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  const canCreateProjects = currentUserRole === 'owner' || currentUserRole === 'admin';

  if (loading && projects.length === 0) {
    return (
      <Box display="flex" justifyContent="center" py={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Projects</Typography>
        {canCreateProjects && (
          <Button
            startIcon={<AddIcon />}
            variant="contained"
            onClick={() => setCreateDialogOpen(true)}
          >
            New Project
          </Button>
        )}
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      {projects.length === 0 ? (
        <Alert severity="info">
          No projects yet. {canCreateProjects ? 'Create your first project!' : 'Ask your administrator to create a project.'}
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project) => (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={project.id}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <FolderIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                      {project.name}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {project.description || 'No description'}
                  </Typography>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="caption" color="text.secondary">
                      Created: {new Date(project.created_at).toLocaleDateString()}
                    </Typography>
                    {project.role && (
                      <Chip
                        label={project.role}
                        size="small"
                        color={project.role === 'owner' ? 'error' : project.role === 'admin' ? 'warning' : 'primary'}
                      />
                    )}
                  </Box>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<VisibilityIcon />}
                    onClick={() => handleViewProject(project.id)}
                  >
                    View Details
                  </Button>
                  {(project.role === 'owner' || project.role === 'admin') && (
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteProject(project.id, project.name)}
                      color="error"
                      title="Delete Project"
                    >
                      <DeleteIcon />
                    </IconButton>
                  )}
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Project Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Project Name"
            fullWidth
            variant="outlined"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && newProjectName.trim() && !loading) {
                handleCreateProject();
              }
            }}
          />
          <Box position="relative">
            <TextField
              margin="dense"
              label="Goals & Description (optional)"
              fullWidth
              multiline
              rows={3}
              variant="outlined"
              value={newProjectDescription}
              onChange={(e) => setNewProjectDescription(e.target.value)}
            />
            <Button
              startIcon={<AIIcon />}
              variant="outlined"
              size="small"
              onClick={() => {
                // TODO: Implement AI project description enhancement
                alert('AI project description enhancement coming soon!');
              }}
              sx={{ position: 'absolute', right: 8, top: 16 }}
            >
              Enhance with AI
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateProject} 
            variant="contained" 
            disabled={!newProjectName.trim() || loading}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};