import React, { useState, useEffect } from 'react';
import {
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Chip,
  CircularProgress,
  Typography,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button
} from '@mui/material';
import { Add as AddIcon, Folder as FolderIcon } from '@mui/icons-material';
import { useOrganization } from '../contexts/OrganizationContext';
import { apiService } from '../services/api';

interface Project {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

const ProjectSelector: React.FC = () => {
  const { currentOrganization } = useOrganization();
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [creating, setCreating] = useState(false);

  // Load projects when organization changes
  useEffect(() => {
    if (currentOrganization) {
      loadProjects();
    } else {
      setProjects([]);
      setCurrentProject(null);
    }
  }, [currentOrganization]);

  // Load current project from localStorage
  useEffect(() => {
    const projectId = localStorage.getItem('currentProjectId');
    if (projectId && projects.length > 0) {
      const project = projects.find(p => p.id === projectId);
      if (project) {
        setCurrentProject(project);
      }
    } else if (projects.length > 0 && !currentProject) {
      // Set first project as current if none selected
      setCurrentProject(projects[0]);
      localStorage.setItem('currentProjectId', projects[0].id);
    }
  }, [projects]);

  const loadProjects = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    try {
      const response = await apiService.projects.list(currentOrganization.id);
      const projectList = response.data.projects || [];
      setProjects(projectList);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProjectChange = (event: any) => {
    const projectId = event.target.value;
    const project = projects.find(p => p.id === projectId);
    if (project) {
      setCurrentProject(project);
      localStorage.setItem('currentProjectId', project.id);
      // Reload page to update all components with new project context
      window.location.reload();
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim() || !currentOrganization) return;
    
    setCreating(true);
    try {
      const response = await apiService.projects.create({
        name: newProjectName.trim(),
        description: newProjectDescription.trim() || undefined,
        organization_id: currentOrganization.id
      });
      
      const newProject = response.data.project;
      setProjects([...projects, newProject]);
      setCurrentProject(newProject);
      localStorage.setItem('currentProjectId', newProject.id);
      
      setCreateDialogOpen(false);
      setNewProjectName('');
      setNewProjectDescription('');
      
      // Reload to ensure all components update
      window.location.reload();
    } catch (error) {
      console.error('Failed to create project:', error);
    } finally {
      setCreating(false);
    }
  };

  if (!currentOrganization) {
    return null;
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
        <CircularProgress size={20} />
      </Box>
    );
  }

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel id="project-select-label">
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <FolderIcon sx={{ fontSize: 18, mr: 0.5 }} />
              Project
            </Box>
          </InputLabel>
          <Select
            labelId="project-select-label"
            id="project-select"
            value={currentProject?.id || ''}
            label="Project"
            onChange={handleProjectChange}
            renderValue={(value) => {
              const project = projects.find(p => p.id === value);
              return project ? (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="body2">{project.name}</Typography>
                </Box>
              ) : null;
            }}
          >
            {projects.length === 0 ? (
              <MenuItem disabled>
                <Typography variant="body2" color="text.secondary">
                  No projects yet
                </Typography>
              </MenuItem>
            ) : (
              projects.map((project) => (
                <MenuItem key={project.id} value={project.id}>
                  <Box>
                    <Typography variant="body2">{project.name}</Typography>
                    {project.description && (
                      <Typography variant="caption" color="text.secondary">
                        {project.description}
                      </Typography>
                    )}
                  </Box>
                </MenuItem>
              ))
            )}
          </Select>
        </FormControl>
        
        <IconButton
          size="small"
          onClick={() => setCreateDialogOpen(true)}
          sx={{ ml: 1 }}
          title="Create new project"
        >
          <AddIcon />
        </IconButton>
      </Box>

      {/* Create Project Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
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
              if (e.key === 'Enter' && newProjectName.trim() && !creating) {
                handleCreateProject();
              }
            }}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description (optional)"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={newProjectDescription}
            onChange={(e) => setNewProjectDescription(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && newProjectName.trim() && !creating) {
                e.preventDefault();
                handleCreateProject();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateProject}
            variant="contained"
            disabled={!newProjectName.trim() || creating}
          >
            {creating ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ProjectSelector;