import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Alert,
  IconButton,
  Collapse,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Close as CloseIcon,
  Folder as FolderIcon,
  Flag as FlagIcon,
  Task as TaskIcon,
  Business as BusinessIcon,
  SmartToy as SmartToyIcon,
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useProject } from '../contexts/ProjectContext';

interface GettingStartedGuideProps {
  onDismiss: () => void;
  completedSteps: Set<string>;
  onStepComplete: (step: string) => void;
}

export const GettingStartedGuide: React.FC<GettingStartedGuideProps> = ({
  onDismiss,
  completedSteps,
  onStepComplete,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { currentProject } = useProject();
  const [activeStep, setActiveStep] = useState(0);
  const [expanded, setExpanded] = useState(true);

  const steps = [
    {
      id: 'create-project',
      label: 'Create Your First Project',
      icon: <FolderIcon />,
      description: 'Start by creating a project and adding a detailed description to help AI agents understand your business context.',
      action: 'Create Project',
      path: '/organization-settings/projects',
      completed: !!currentProject,
    },
    {
      id: 'set-goals',
      label: 'Define Your Goals',
      icon: <FlagIcon />,
      description: 'Set clear, measurable goals for your project. These will guide the AI agents and help track progress.',
      action: 'Add Goals',
      path: currentProject ? `/projects/${currentProject.id}/goals` : null,
      completed: completedSteps.has('set-goals'),
    },
    {
      id: 'add-tasks',
      label: 'Create Tasks',
      icon: <TaskIcon />,
      description: 'Break down your goals into actionable tasks. Use the AI Generate Tasks button for smart suggestions.',
      action: 'Add Tasks',
      path: currentProject ? `/projects/${currentProject.id}/tasks` : null,
      completed: completedSteps.has('add-tasks'),
    },
    {
      id: 'setup-department',
      label: 'Setup Departments',
      icon: <BusinessIcon />,
      description: 'Organize your team by creating departments for different areas of your business.',
      action: 'Create Department',
      path: currentProject ? `/projects/${currentProject.id}/departments` : null,
      completed: completedSteps.has('setup-department'),
    },
    {
      id: 'assign-agents',
      label: 'Assign AI Agents',
      icon: <SmartToyIcon />,
      description: 'Assign specialized AI agents to departments to automate workflows and boost productivity.',
      action: 'Assign Agents',
      path: currentProject ? `/projects/${currentProject.id}/departments` : null,
      completed: completedSteps.has('assign-agents'),
    },
  ];

  const completedCount = steps.filter(step => step.completed).length;
  const progress = (completedCount / steps.length) * 100;

  const handleAction = (step: typeof steps[0]) => {
    if (step.path) {
      navigate(step.path);
      onStepComplete(step.id);
    }
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  return (
    <Card sx={{ mb: 3, position: 'relative' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flex={1}>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Typography variant="h6" component="h2">
                Welcome to AICOS! 🚀
              </Typography>
              <IconButton
                size="small"
                onClick={() => setExpanded(!expanded)}
                sx={{ ml: 'auto' }}
              >
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
              <IconButton
                size="small"
                onClick={onDismiss}
                title="Dismiss guide"
              >
                <CloseIcon />
              </IconButton>
            </Box>
            
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <LinearProgress 
                variant="determinate" 
                value={progress} 
                sx={{ flex: 1, height: 8, borderRadius: 4 }}
              />
              <Chip
                label={`${completedCount}/${steps.length}`}
                size="small"
                color={completedCount === steps.length ? 'success' : 'default'}
              />
            </Box>
          </Box>
        </Box>

        <Collapse in={expanded}>
          {completedCount === steps.length ? (
            <Alert 
              severity="success" 
              icon={<CheckCircleIcon />}
              sx={{ mb: 2 }}
            >
              Congratulations! You've completed all the setup steps. Your AI-powered business automation is ready to go!
            </Alert>
          ) : (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Follow these steps to get your AI-powered business up and running:
              </Typography>

              <Stepper activeStep={activeStep} orientation="vertical">
                {steps.map((step, index) => (
                  <Step key={step.id} completed={step.completed}>
                    <StepLabel
                      StepIconComponent={() => (
                        <Box
                          sx={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            bgcolor: step.completed 
                              ? 'success.main' 
                              : activeStep === index 
                              ? 'primary.main' 
                              : 'grey.300',
                            color: 'white',
                          }}
                        >
                          {step.completed ? <CheckCircleIcon /> : step.icon}
                        </Box>
                      )}
                    >
                      <Typography variant="subtitle1" fontWeight="medium">
                        {step.label}
                      </Typography>
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {step.description}
                      </Typography>
                      <Box sx={{ mb: 2 }}>
                        <Button
                          variant="contained"
                          onClick={() => handleAction(step)}
                          disabled={!step.path}
                          size="small"
                        >
                          {step.action}
                        </Button>
                        {index > 0 && (
                          <Button
                            disabled={index === 0}
                            onClick={handleBack}
                            sx={{ ml: 1 }}
                            size="small"
                          >
                            Back
                          </Button>
                        )}
                        {index < steps.length - 1 && (
                          <Button
                            variant="text"
                            onClick={handleNext}
                            sx={{ ml: 1 }}
                            size="small"
                          >
                            Skip
                          </Button>
                        )}
                      </Box>
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </>
          )}
        </Collapse>
      </CardContent>
    </Card>
  );
};