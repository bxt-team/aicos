import React, { useState } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  Paper,
  TextField,
  Container,
  Alert,
  CircularProgress,
  Fade,
  Grow
} from '@mui/material';
import {
  Business as BusinessIcon,
  Folder as FolderIcon,
  CheckCircle as CheckCircleIcon,
  RocketLaunch as RocketIcon
} from '@mui/icons-material';
import { useOrganization } from '../contexts/OrganizationContext';

const steps = ['Create Organization', 'Create Project', 'Get Started'];

interface OnboardingWizardProps {
  onComplete: () => void;
}

const OnboardingWizard: React.FC<OnboardingWizardProps> = ({ onComplete }) => {
  const { createOrganization, currentOrganization, createProject } = useOrganization();
  
  // Start at step 1 if organization already exists
  const [activeStep, setActiveStep] = useState(currentOrganization ? 1 : 0);
  const [orgName, setOrgName] = useState('');
  const [orgDescription, setOrgDescription] = useState('');
  const [projectName, setProjectName] = useState('Default Project');
  const [projectDescription, setProjectDescription] = useState('Your first project - feel free to rename or create additional projects');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateOrganization = async () => {
    if (!orgName.trim()) {
      setError('Organization name is required');
      return;
    }
    
    setIsCreating(true);
    setError(null);
    
    try {
      await createOrganization({ 
        name: orgName.trim(), 
        description: orgDescription.trim() || undefined 
      });
      setActiveStep(1);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to create organization';
      setError(typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  const handleCreateProject = async () => {
    if (!projectName.trim() || !currentOrganization) {
      setError('Project name is required');
      return;
    }
    
    setIsCreating(true);
    setError(null);
    
    try {
      const newProject = await createProject({
        name: projectName.trim(),
        description: projectDescription.trim() || undefined,
        organization_id: currentOrganization.id
      });
      // Store the project ID immediately
      if (newProject?.id) {
        localStorage.setItem('currentProjectId', newProject.id);
      }
      setActiveStep(2);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to create project';
      setError(typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Fade in={true} timeout={500}>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <BusinessIcon sx={{ fontSize: 48, mr: 2, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h5" gutterBottom>
                    Welcome! Let's set up your organization
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    An organization is your workspace where you can manage projects and collaborate with your team.
                  </Typography>
                </Box>
              </Box>
              
              <TextField
                fullWidth
                label="Organization Name"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && orgName.trim() && !isCreating) {
                    handleCreateOrganization();
                  }
                }}
                placeholder="e.g. My Company, Personal Workspace"
                required
                sx={{ mb: 3 }}
                autoFocus
              />
              
              <TextField
                fullWidth
                label="Description (optional)"
                value={orgDescription}
                onChange={(e) => setOrgDescription(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey && orgName.trim() && !isCreating) {
                    e.preventDefault();
                    handleCreateOrganization();
                  }
                }}
                placeholder="What does your organization do?"
                multiline
                rows={3}
                sx={{ mb: 3 }}
              />
            </Box>
          </Fade>
        );
        
      case 1:
        return (
          <Fade in={true} timeout={500}>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <FolderIcon sx={{ fontSize: 48, mr: 2, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h5" gutterBottom>
                    Create your first project
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Projects help you organize your work. You can create multiple projects within your organization.
                  </Typography>
                </Box>
              </Box>
              
              <Alert severity="success" sx={{ mb: 3 }}>
                Organization "{currentOrganization?.name}" created successfully!
              </Alert>
              
              <TextField
                fullWidth
                label="Project Name"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && projectName.trim() && !isCreating) {
                    handleCreateProject();
                  }
                }}
                placeholder="e.g. Marketing Campaign, Content Strategy"
                required
                sx={{ mb: 3 }}
                autoFocus
              />
              
              <TextField
                fullWidth
                label="Description (optional)"
                value={projectDescription}
                onChange={(e) => setProjectDescription(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey && projectName.trim() && !isCreating) {
                    e.preventDefault();
                    handleCreateProject();
                  }
                }}
                placeholder="What is this project about?"
                multiline
                rows={3}
                sx={{ mb: 3 }}
              />
            </Box>
          </Fade>
        );
        
      case 2:
        return (
          <Grow in={true} timeout={800}>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 3 }} />
              <Typography variant="h4" gutterBottom>
                All set! You're ready to go
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Your organization and project have been created successfully.
              </Typography>
              <Box sx={{ mt: 4, p: 3, bgcolor: 'background.paper', borderRadius: 2, border: 1, borderColor: 'divider' }}>
                <RocketIcon sx={{ fontSize: 40, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Start using AI Agents
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  You can now access all AI features including content generation, social media management, and more.
                </Typography>
              </Box>
            </Box>
          </Grow>
        );
        
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ width: '100%', pt: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          
          <Box sx={{ minHeight: 400 }}>
            {getStepContent(activeStep)}
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
            {activeStep === 0 && (
              <Button
                variant="contained"
                onClick={handleCreateOrganization}
                disabled={!orgName.trim() || isCreating}
                size="large"
                startIcon={isCreating ? <CircularProgress size={20} /> : null}
              >
                {isCreating ? 'Creating...' : 'Create Organization'}
              </Button>
            )}
            
            {activeStep === 1 && (
              <Button
                variant="contained"
                onClick={handleCreateProject}
                disabled={!projectName.trim() || isCreating}
                size="large"
                startIcon={isCreating ? <CircularProgress size={20} /> : null}
              >
                {isCreating ? 'Creating...' : 'Create Project'}
              </Button>
            )}
            
            {activeStep === 2 && (
              <Button
                variant="contained"
                onClick={() => {
                  console.log('OnboardingWizard: Get Started clicked, calling onComplete');
                  onComplete();
                }}
                size="large"
                color="success"
              >
                Get Started
              </Button>
            )}
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default OnboardingWizard;