import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Box, Paper, Typography, Alert, Button } from '@mui/material';
import { FolderOpen as ProjectIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface ProjectRequiredProps {
  children: React.ReactNode;
  message?: string;
}

const ProjectRequired: React.FC<ProjectRequiredProps> = ({ 
  children, 
  message = "Sie müssen ein Projekt auswählen, um diese Funktion zu nutzen." 
}) => {
  const { currentProject, isLoading } = useAuth();
  const navigate = useNavigate();

  // Still loading, show nothing or a loader
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Typography color="text.secondary">Lade...</Typography>
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
            Kein Projekt ausgewählt
          </Typography>
          <Alert severity="info" sx={{ mt: 2, mb: 3 }}>
            {message}
          </Alert>
          <Typography variant="body1" color="text.secondary" paragraph>
            Bitte wählen Sie ein Projekt aus dem Dropdown-Menü in der Kopfzeile aus oder erstellen Sie ein neues Projekt.
          </Typography>
          <Button 
            variant="contained" 
            onClick={() => navigate('/')}
            sx={{ mt: 2 }}
          >
            Zurück zur Übersicht
          </Button>
        </Paper>
      </Box>
    );
  }

  // Project is selected, render children
  return <>{children}</>;
};

export default ProjectRequired;