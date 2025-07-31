import React from 'react';
import { useParams } from 'react-router-dom';
import { Container, Paper, Box, Typography, Button } from '@mui/material';
import { ArrowBack as ArrowBackIcon, Flag as FlagIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { GoalsManagement } from './GoalsManagement';

const ProjectGoals: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  return (
    <Container maxWidth="lg" sx={{ mt: 3 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" mb={3}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(`/projects/${projectId}`)}
            sx={{ mr: 2 }}
          >
            Back to Project
          </Button>
          <FlagIcon sx={{ mr: 1 }} />
          <Typography variant="h5" component="h1">
            Project Goals
          </Typography>
        </Box>
        
        <GoalsManagement projectId={projectId} />
      </Paper>
    </Container>
  );
};

export default ProjectGoals;