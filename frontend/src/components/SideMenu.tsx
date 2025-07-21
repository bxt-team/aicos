import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { getEnabledAgents, getAgentsByCategory, getAgentByRoute } from '../config/agents';
import { useMenu } from '../contexts/MenuContext';
import { useAuth } from '../contexts/AuthContext';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
  Box,
  Typography
} from '@mui/material';
import { Business as BusinessIcon, FolderOpen as ProjectIcon } from '@mui/icons-material';
import axios from 'axios';
import './SideMenu.css';

const SideMenu: React.FC = () => {
  const { isMenuOpen: isExpanded, toggleMenu, isMobile } = useMenu();
  const location = useLocation();
  const { currentOrganization, setCurrentOrganization, currentProject, setCurrentProject, user, isLoading } = useAuth();
  const [createOrgOpen, setCreateOrgOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Check if organization and project exist when user is logged in
  useEffect(() => {
    console.log('SideMenu: Loading:', isLoading);
    console.log('SideMenu: User:', user);
    console.log('SideMenu: Current organization:', currentOrganization);
    console.log('SideMenu: Current project:', currentProject);
    console.log('SideMenu: Should show create org dialog:', !isLoading && user && !currentOrganization);
    console.log('SideMenu: Should show create project dialog:', !isLoading && user && currentOrganization && !currentProject);
    
    // Only show dialog after loading is complete
    if (!isLoading && user) {
      if (!currentOrganization) {
        console.log('SideMenu: Opening create organization dialog');
        setCreateOrgOpen(true);
      } else if (!currentProject) {
        console.log('SideMenu: Opening create project dialog');
        setCreateProjectOpen(true);
      }
    }
  }, [user, currentOrganization, currentProject, isLoading]);

  // Close menu on route change for mobile
  useEffect(() => {
    if (isMobile && isExpanded) {
      toggleMenu();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // Prevent body scroll when menu is open on mobile
  useEffect(() => {
    if (isMobile && isExpanded) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobile, isExpanded]);

  const handleOverlayClick = () => {
    if (isMobile && isExpanded) {
      toggleMenu();
    }
  };

  const agents = getEnabledAgents();
  const agentsByCategory = getAgentsByCategory();
  const categories = Object.keys(agentsByCategory);
  
  const getCurrentAgent = () => {
    return getAgentByRoute(location.pathname);
  };

  const currentAgent = getCurrentAgent();

  const handleToggleClick = () => {
    toggleMenu();
  };

  const handleCreateOrg = async () => {
    if (!newOrgName.trim()) return;
    
    setIsCreating(true);
    try {
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${baseURL}/api/organizations`, {
        name: newOrgName
      });
      
      const newOrg = response.data.organization;
      setCurrentOrganization(newOrg);
      setCreateOrgOpen(false);
      setNewOrgName('');
      
      // Reload to get updated user data with new organization
      window.location.reload();
    } catch (error) {
      console.error('Failed to create organization:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim() || !currentOrganization) return;
    
    setIsCreating(true);
    try {
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${baseURL}/api/projects`, {
        name: newProjectName,
        description: newProjectDescription,
        organization_id: currentOrganization.id
      });
      
      const newProject = response.data.project;
      setCurrentProject(newProject);
      setCreateProjectOpen(false);
      setNewProjectName('');
      setNewProjectDescription('');
    } catch (error) {
      console.error('Failed to create project:', error);
    } finally {
      setIsCreating(false);
    }
  };

  // Don't render agent menu if no organization or project is selected (after loading is complete)
  if (!isLoading && user && (!currentOrganization || !currentProject)) {
    return (
      <>
        {/* Organization Creation Dialog */}
        <Dialog 
          open={createOrgOpen && !currentOrganization} 
          onClose={() => {}} // Prevent closing by clicking outside
          disableEscapeKeyDown // Prevent closing with ESC key
          fullWidth
          maxWidth="sm"
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BusinessIcon color="primary" />
              <Typography variant="h6">Organisation erstellen</Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            <Alert severity="info" sx={{ mb: 3 }}>
              Sie müssen zuerst eine Organisation erstellen, bevor Sie die AI-Agenten nutzen können.
            </Alert>
            <TextField
              autoFocus
              margin="dense"
              label="Organisationsname"
              fullWidth
              variant="outlined"
              value={newOrgName}
              onChange={(e) => setNewOrgName(e.target.value)}
              placeholder="z.B. Meine Firma, Persönlicher Workspace"
              disabled={isCreating}
            />
          </DialogContent>
          <DialogActions>
            <Button 
              onClick={handleCreateOrg} 
              variant="contained" 
              disabled={!newOrgName.trim() || isCreating}
              size="large"
            >
              {isCreating ? 'Wird erstellt...' : 'Organisation erstellen'}
            </Button>
          </DialogActions>
        </Dialog>
        
        {/* Project Creation Dialog */}
        <Dialog 
          open={createProjectOpen && !!currentOrganization && !currentProject} 
          onClose={() => {}} // Prevent closing by clicking outside
          disableEscapeKeyDown // Prevent closing with ESC key
          fullWidth
          maxWidth="sm"
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ProjectIcon color="primary" />
              <Typography variant="h6">Projekt erstellen</Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            <Alert severity="info" sx={{ mb: 3 }}>
              Sie müssen ein Projekt erstellen, um die AI-Agenten nutzen zu können.
            </Alert>
            <TextField
              autoFocus
              margin="dense"
              label="Projektname"
              fullWidth
              variant="outlined"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="z.B. Marketing Kampagne, Content Strategie"
              disabled={isCreating}
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
              disabled={isCreating}
            />
          </DialogContent>
          <DialogActions>
            <Button 
              onClick={handleCreateProject} 
              variant="contained" 
              disabled={!newProjectName.trim() || isCreating}
              size="large"
            >
              {isCreating ? 'Wird erstellt...' : 'Projekt erstellen'}
            </Button>
          </DialogActions>
        </Dialog>
        
        <aside className="side-menu collapsed">
          <div className="side-menu-header">
            <div className="no-org-message">
              <Typography variant="body2" color="text.secondary">
                {!currentOrganization 
                  ? 'Bitte erstellen Sie eine Organisation'
                  : 'Bitte erstellen Sie ein Projekt'
                }
              </Typography>
            </div>
          </div>
        </aside>
      </>
    );
  }

  return (
    <>
      {/* Mobile overlay */}
      {isMobile && isExpanded && (
        <div className="menu-overlay" onClick={handleOverlayClick} />
      )}
      
      <aside className={`side-menu ${isExpanded ? 'expanded' : 'collapsed'} ${isMobile ? 'mobile' : ''}`}>
      <div className="side-menu-header">
        <button 
          className="menu-toggle"
          onClick={handleToggleClick}
          aria-label={isExpanded ? 'Menü einklappen' : 'Menü ausklappen'}
        >
          {isExpanded ? '◀' : '▶'}
        </button>
        {isExpanded && (
          <div className="menu-title">
            <h3>🤖 AI Agenten</h3>
            <p className="agent-count">{agents.length} verfügbar</p>
            {isMobile && (
              <button 
                className="menu-close"
                onClick={handleToggleClick}
                aria-label="Menü schließen"
              >
                ✕
              </button>
            )}
          </div>
        )}
      </div>

      <nav className="side-menu-nav">
        {isExpanded ? (
          <>
            {categories.map(category => (
              <div key={category} className="menu-category">
                <h4 className="category-title">{category}</h4>
                <ul className="agents-list">
                  {agentsByCategory[category].map(agent => (
                    <li key={agent.id}>
                      <Link
                        to={agent.route}
                        className={`menu-item ${location.pathname === agent.route ? 'active' : ''}`}
                        title={agent.description}
                      >
                        <span className="agent-icon">{agent.icon}</span>
                        <div className="agent-info">
                          <span className="agent-name">{agent.name}</span>
                          <span className="agent-description">{agent.description}</span>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </>
        ) : (
          <ul className="agents-list-collapsed">
            {agents.map(agent => (
              <li key={agent.id}>
                <Link
                  to={agent.route}
                  className={`menu-item-collapsed ${location.pathname === agent.route ? 'active' : ''}`}
                  title={agent.name}
                >
                  <span className="agent-icon">{agent.icon}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </nav>
    </aside>
    </>
  );
};

export default SideMenu;