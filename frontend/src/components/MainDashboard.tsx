import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Business as BusinessIcon,
  Folder as FolderIcon,
  People as PeopleIcon,
  CreditCard as CreditCardIcon,
  Add as AddIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { useProject } from '../contexts/ProjectContext';
import { GettingStartedGuide } from './GettingStartedGuide';
import api from '../services/api';

const MainDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSupabaseAuth();
  const { currentOrganization, organizations } = useOrganization();
  const { currentProject, projects } = useProject();
  const [showGettingStarted, setShowGettingStarted] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());

  // Quick stats
  const stats = {
    organizations: organizations.length,
    projects: projects.length,
  };

  // Check if user is new (show getting started guide)
  useEffect(() => {
    const checkOnboardingStatus = async () => {
      try {
        // Check if user has completed onboarding
        const onboardingCompleted = localStorage.getItem('onboarding_completed');
        const hasProjects = projects.length > 0;
        
        // Show guide if: no onboarding completion flag OR no projects
        if (!onboardingCompleted || !hasProjects) {
          setShowGettingStarted(true);
        }

        // Check completed steps
        const steps = new Set<string>();
        if (hasProjects) steps.add('create-project');
        
        // Check for goals and tasks if there's a current project
        if (currentProject) {
          try {
            const goalsResponse = await api.get(`/api/goals?project_id=${currentProject.id}`);
            if (goalsResponse.data && goalsResponse.data.length > 0) {
              steps.add('set-goals');
            }

            const tasksResponse = await api.get(`/api/tasks?project_id=${currentProject.id}`);
            if (tasksResponse.data && tasksResponse.data.length > 0) {
              steps.add('add-tasks');
            }

            const deptResponse = await api.get(`/api/departments?project_id=${currentProject.id}`);
            if (deptResponse.data && deptResponse.data.length > 0) {
              steps.add('setup-department');
              
              // Check if any department has agents assigned
              const hasAgents = deptResponse.data.some((dept: any) => dept.ai_agent_count > 0);
              if (hasAgents) {
                steps.add('assign-agents');
              }
            }
          } catch (error) {
            console.error('Error checking onboarding steps:', error);
          }
        }
        
        setCompletedSteps(steps);
      } catch (error) {
        console.error('Error checking onboarding status:', error);
      }
    };

    checkOnboardingStatus();
  }, [projects, currentProject]);

  const handleDismissGuide = () => {
    setShowGettingStarted(false);
    localStorage.setItem('onboarding_completed', 'true');
  };

  const handleStepComplete = (step: string) => {
    setCompletedSteps(prev => {
      const newSet = new Set(prev);
      newSet.add(step);
      return newSet;
    });
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          <DashboardIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Welcome back{user?.user_metadata?.name ? `, ${user.user_metadata.name}` : ''}!
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Here's your workspace overview
        </Typography>
      </Box>

      {/* Getting Started Guide */}
      {showGettingStarted && (
        <GettingStartedGuide
          onDismiss={handleDismissGuide}
          completedSteps={completedSteps}
          onStepComplete={handleStepComplete}
        />
      )}

      {/* Current Context */}
      {currentOrganization && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography>
              Currently viewing: <strong>{currentOrganization.name}</strong>
              {currentProject && <> / <strong>{currentProject.name}</strong></>}
            </Typography>
            <Button
              size="small"
              onClick={() => navigate('/organization-settings/projects')}
            >
              Switch Project
            </Button>
          </Box>
        </Alert>
      )}

      {/* Stats Cards */}
      <Box display="flex" flexWrap="wrap" gap={3} mb={4}>
        <Box flex="1 1 250px">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Organizations
                  </Typography>
                  <Typography variant="h4">
                    {stats.organizations}
                  </Typography>
                </Box>
                <BusinessIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box flex="1 1 250px">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Projects
                  </Typography>
                  <Typography variant="h4">
                    {stats.projects}
                  </Typography>
                </Box>
                <FolderIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box flex="1 1 250px">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    AI Agents
                  </Typography>
                  <Typography variant="h4">
                    12
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Available
                  </Typography>
                </Box>
                <AssignmentIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box flex="1 1 250px">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Credits
                  </Typography>
                  <Button
                    size="small"
                    sx={{ mt: 1 }}
                    onClick={() => navigate('/organization-settings/billing')}
                  >
                    View Usage
                  </Button>
                </Box>
                <CreditCardIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Quick Actions and Recent Projects */}
      <Box display="flex" flexWrap="wrap" gap={3}>
        <Box flex="1 1 400px">
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <List>
              {currentProject ? (
                <ListItem disablePadding>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<FolderIcon />}
                    onClick={() => navigate(`/projects/${currentProject.id}`)}
                  >
                    Go to Current Project
                  </Button>
                </ListItem>
              ) : (
                <ListItem disablePadding>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => navigate('/organization-settings/projects')}
                  >
                    Create Your First Project
                  </Button>
                </ListItem>
              )}
              <ListItem disablePadding sx={{ mt: 1 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<PeopleIcon />}
                  onClick={() => navigate('/organization-settings/members')}
                >
                  Manage Team Members
                </Button>
              </ListItem>
              <ListItem disablePadding sx={{ mt: 1 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<BusinessIcon />}
                  onClick={() => navigate('/organization-settings/departments')}
                >
                  Manage Departments
                </Button>
              </ListItem>
            </List>
          </Paper>
        </Box>

        <Box flex="1 1 400px">
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Recent Projects
            </Typography>
            {projects.length === 0 ? (
              <Typography color="textSecondary">
                No projects yet. Create your first project to get started!
              </Typography>
            ) : (
              <List>
                {projects.slice(0, 5).map((project) => (
                  <ListItemButton
                    key={project.id}
                    onClick={() => navigate(`/projects/${project.id}`)}
                  >
                    <ListItemIcon>
                      <FolderIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={project.name}
                      secondary={project.description || 'No description'}
                    />
                  </ListItemButton>
                ))}
              </List>
            )}
          </Paper>
        </Box>
      </Box>
    </Container>
  );
};

export default MainDashboard;