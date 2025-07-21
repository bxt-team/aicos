import React, { useState, useEffect } from 'react';
import {
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Typography,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress
} from '@mui/material';
import { Add as AddIcon, Business as BusinessIcon } from '@mui/icons-material';
import axios from 'axios';
import { useAuth, Project } from '../contexts/AuthContext';

const OrganizationSelector: React.FC = () => {
  const { currentOrganization, setCurrentOrganization, currentProject, setCurrentProject, user } = useAuth();
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoadingOrgs, setIsLoadingOrgs] = useState(true);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [createOrgOpen, setCreateOrgOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');

  // Load organizations
  useEffect(() => {
    const loadOrganizations = async () => {
      try {
        const response = await axios.get('/api/organizations');
        setOrganizations(response.data.organizations);
      } catch (error) {
        console.error('Failed to load organizations:', error);
      } finally {
        setIsLoadingOrgs(false);
      }
    };

    if (user) {
      loadOrganizations();
    }
  }, [user]);

  // Load projects when organization changes
  useEffect(() => {
    const loadProjects = async () => {
      if (!currentOrganization) return;
      
      setIsLoadingProjects(true);
      try {
        const response = await axios.get('/api/projects', {
          params: { organization_id: currentOrganization.id }
        });
        setProjects(response.data.projects);
        
        // Auto-select first project if none selected
        if (response.data.projects.length > 0 && !currentProject) {
          setCurrentProject(response.data.projects[0]);
        }
      } catch (error) {
        console.error('Failed to load projects:', error);
      } finally {
        setIsLoadingProjects(false);
      }
    };

    loadProjects();
  }, [currentOrganization]);

  const handleOrgChange = (orgId: string) => {
    const org = organizations.find(o => o.id === orgId);
    if (org) {
      setCurrentOrganization(org);
      setCurrentProject(null); // Reset project selection
    }
  };

  const handleProjectChange = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    if (project) {
      setCurrentProject(project);
    }
  };

  const handleCreateOrg = async () => {
    try {
      const response = await axios.post('/api/organizations', {
        name: newOrgName
      });
      
      // Add new org to list and select it
      const newOrg = response.data.organization;
      setOrganizations([...organizations, newOrg]);
      setCurrentOrganization(newOrg);
      setCreateOrgOpen(false);
      setNewOrgName('');
    } catch (error) {
      console.error('Failed to create organization:', error);
    }
  };

  const handleCreateProject = async () => {
    if (!currentOrganization) return;
    
    try {
      const response = await axios.post('/api/projects', {
        name: newProjectName,
        description: newProjectDescription,
        organization_id: currentOrganization.id
      });
      
      // Add new project to list and select it
      const newProject = response.data.project;
      setProjects([...projects, newProject]);
      setCurrentProject(newProject);
      setCreateProjectOpen(false);
      setNewProjectName('');
      setNewProjectDescription('');
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  if (isLoadingOrgs) {
    return <CircularProgress size={20} />;
  }

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
      {/* Organization Selector */}
      <FormControl size="small" sx={{ minWidth: 200 }}>
        <InputLabel id="org-select-label">
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <BusinessIcon fontSize="small" />
            Organisation
          </Box>
        </InputLabel>
        <Select
          labelId="org-select-label"
          value={currentOrganization?.id || ''}
          onChange={(e) => handleOrgChange(e.target.value)}
          label="Organisation"
        >
          {organizations.map((org) => (
            <MenuItem key={org.id} value={org.id}>
              {org.name}
              {org.role && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                  ({org.role})
                </Typography>
              )}
            </MenuItem>
          ))}
          <Divider />
          <MenuItem onClick={() => setCreateOrgOpen(true)}>
            <AddIcon fontSize="small" sx={{ mr: 1 }} />
            Neue Organisation
          </MenuItem>
        </Select>
      </FormControl>

      {/* Project Selector */}
      {currentOrganization && (
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel id="project-select-label">Projekt</InputLabel>
          <Select
            labelId="project-select-label"
            value={currentProject?.id || ''}
            onChange={(e) => handleProjectChange(e.target.value)}
            label="Projekt"
            disabled={isLoadingProjects}
          >
            {projects.map((project) => (
              <MenuItem key={project.id} value={project.id}>
                {project.name}
              </MenuItem>
            ))}
            <Divider />
            <MenuItem onClick={() => setCreateProjectOpen(true)}>
              <AddIcon fontSize="small" sx={{ mr: 1 }} />
              Neues Projekt
            </MenuItem>
          </Select>
        </FormControl>
      )}

      {/* Create Organization Dialog */}
      <Dialog open={createOrgOpen} onClose={() => setCreateOrgOpen(false)}>
        <DialogTitle>Neue Organisation erstellen</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Organisationsname"
            fullWidth
            variant="outlined"
            value={newOrgName}
            onChange={(e) => setNewOrgName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOrgOpen(false)}>Abbrechen</Button>
          <Button onClick={handleCreateOrg} variant="contained" disabled={!newOrgName}>
            Erstellen
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Project Dialog */}
      <Dialog open={createProjectOpen} onClose={() => setCreateProjectOpen(false)}>
        <DialogTitle>Neues Projekt erstellen</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Projektname"
            fullWidth
            variant="outlined"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
          />
          <TextField
            margin="dense"
            label="Beschreibung (optional)"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={newProjectDescription}
            onChange={(e) => setNewProjectDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateProjectOpen(false)}>Abbrechen</Button>
          <Button onClick={handleCreateProject} variant="contained" disabled={!newProjectName}>
            Erstellen
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OrganizationSelector;