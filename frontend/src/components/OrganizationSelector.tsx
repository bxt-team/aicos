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
  const [isLoadingOrgs, setIsLoadingOrgs] = useState(false);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [createOrgOpen, setCreateOrgOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');

  // Load organizations from user data
  useEffect(() => {
    console.log('OrganizationSelector: User data:', user);
    console.log('OrganizationSelector: Current organization:', currentOrganization);
    
    if (user && user.organizations) {
      // Transform the organizations from the user object to the expected format
      const orgs = user.organizations.map((membership: any) => {
        // Handle both nested and flat organization structure
        const org = membership.organization || membership;
        return {
          id: org.id,
          name: org.name,
          description: org.description,
          role: membership.role || org.role,
          created_at: org.created_at
        };
      });
      console.log('OrganizationSelector: Transformed organizations:', orgs);
      setOrganizations(orgs);
      
      // If no current organization is set but we have organizations, set the first one
      if (!currentOrganization && orgs.length > 0) {
        console.log('OrganizationSelector: Setting first organization as current');
        setCurrentOrganization(orgs[0]);
      }
    } else {
      console.log('OrganizationSelector: No user or organizations data');
    }
  }, [user]);

  // Load projects when organization changes
  useEffect(() => {
    const loadProjects = async () => {
      if (!currentOrganization) return;
      
      console.log('OrganizationSelector: Loading projects for organization:', currentOrganization.id);
      setIsLoadingProjects(true);
      try {
        const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        const response = await axios.get(`${baseURL}/api/projects`, {
          params: { organization_id: currentOrganization.id }
        });
        console.log('OrganizationSelector: Projects loaded:', response.data.projects);
        setProjects(response.data.projects);
        
        // If no projects exist, create a default one
        if (response.data.projects.length === 0) {
          const newProjectResponse = await axios.post(`${baseURL}/api/projects`, {
            name: 'Default Project',
            description: 'Your first project - feel free to rename or create additional projects',
            organization_id: currentOrganization.id
          });
          
          const newProject = newProjectResponse.data.project;
          setProjects([newProject]);
          setCurrentProject(newProject);
        } else {
          // Try to restore saved project
          const savedProjectId = localStorage.getItem('currentProjectId');
          if (savedProjectId) {
            const savedProject = response.data.projects.find((p: Project) => p.id === savedProjectId);
            if (savedProject) {
              setCurrentProject(savedProject);
            } else if (!currentProject) {
              // Saved project not found, select first
              setCurrentProject(response.data.projects[0]);
            }
          } else if (!currentProject || !response.data.projects.find((p: Project) => p.id === currentProject.id)) {
            // No saved project and no current project, select first
            setCurrentProject(response.data.projects[0]);
          }
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
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${baseURL}/api/organizations`, {
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
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${baseURL}/api/projects`, {
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
          displayEmpty
        >
          {organizations.length === 0 && (
            <MenuItem value="" disabled>
              <em>Keine Organisation verfügbar</em>
            </MenuItem>
          )}
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
            displayEmpty
          >
            {isLoadingProjects ? (
              <MenuItem value="" disabled>
                <em>Lade Projekte...</em>
              </MenuItem>
            ) : projects.length === 0 ? (
              <MenuItem value="" disabled>
                <em>Keine Projekte verfügbar</em>
              </MenuItem>
            ) : null}
            {projects.map((project) => (
              <MenuItem key={project.id} value={project.id}>
                {project.name}
              </MenuItem>
            ))}
            {projects.length > 0 && <Divider />}
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