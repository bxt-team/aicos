import React from 'react';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { Box, Paper, Typography, Alert, Button } from '@mui/material';
import { FolderOpen as ProjectIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface ProjectRequiredProps {
  children: React.ReactNode;
  message?: string;
}

const ProjectRequired: React.FC<ProjectRequiredProps> = ({ 
  children, 
  message = "You must select a project to use this feature." 
}) => {
  const { loading } = useSupabaseAuth();
  // TODO: Add organization support later
  const currentProject: any = null;
  const navigate = useNavigate();

  // Still loading, show nothing or a loader
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Typography color="text.secondary">Loading...</Typography>
      </Box>
    );
  }

  // No project selected, show message
  if (!currentProject) {
    return (
      <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4, p: 3 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <ProjectIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            No Project Selected
          </Typography>
          <Alert severity="info" sx={{ mt: 2, mb: 3 }}>
            {message}
          </Alert>
          <Typography variant="body1" color="text.secondary" paragraph>
            Please select a project from the dropdown menu in the header or create a new project.
          </Typography>
          <Button 
            variant="contained" 
            onClick={() => navigate('/')}
            sx={{ mt: 2 }}
          >
            Back to Overview
          </Button>
        </Paper>
      </Box>
    );
  }

  // Project is selected, render children
  return <>{children}</>;
};

export default ProjectRequired;