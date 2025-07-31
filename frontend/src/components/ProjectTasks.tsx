import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  IconButton,
  Breadcrumbs,
  Link,
  Alert,
} from '@mui/material';
import {
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useOrganization } from '../contexts/OrganizationContext';
import { useProject } from '../contexts/ProjectContext';
import { TaskManagement } from './TaskManagement';
import { useTranslation } from 'react-i18next';

export default function ProjectTasks() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const { currentOrganization } = useOrganization();
  const { projects } = useProject();
  
  const project = projects.find(p => p.id === projectId);

  if (!project) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Project not found</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box mb={3}>
        <Breadcrumbs aria-label="breadcrumb">
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/organization-settings/projects')}
            sx={{ textDecoration: 'none', cursor: 'pointer' }}
          >
            {currentOrganization?.name}
          </Link>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate(`/projects/${projectId}`)}
            sx={{ textDecoration: 'none', cursor: 'pointer' }}
          >
            {project.name}
          </Link>
          <Typography color="text.primary">{t('task.tasks')}</Typography>
        </Breadcrumbs>
      </Box>

      <Paper elevation={3} sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" mb={3}>
          <Typography variant="h5">
            {project.name} - {t('task.tasks')}
          </Typography>
        </Box>

        <TaskManagement projectId={projectId} />
      </Paper>
    </Container>
  );
}