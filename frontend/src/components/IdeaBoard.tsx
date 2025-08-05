import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Chip,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  LinearProgress,
  Alert,
  ToggleButton,
  ToggleButtonGroup,
  Fab
} from '@mui/material';
import {
  Add as AddIcon,
  Lightbulb as IdeaIcon,
  Business as CompanyIcon,
  Folder as ProjectIcon,
  FilterList as FilterIcon,
  CheckCircle as ValidatedIcon,
  Cancel as RejectedIcon,
  Task as TaskIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ViewModule as GridViewIcon,
  ViewList as ListViewIcon,
  TrendingUp as ScoreIcon
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import './IdeaBoard.css';

interface Idea {
  id: string;
  title: string;
  initial_description: string;
  refined_description?: string;
  status: string;
  validation_score?: number;
  validation_reasons?: any;
  conversation_history: any[];
  project_id?: string;
  created_at: string;
  updated_at: string;
}

interface Project {
  id: string;
  name: string;
}

const IdeaBoard: React.FC = () => {
  const navigate = useNavigate();
  const { session } = useSupabaseAuth();
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProject, setSelectedProject] = useState<string>('all');

  useEffect(() => {
    fetchIdeas();
    fetchProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchIdeas = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/ideas`, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch ideas');
      }

      const data = await response.json();
      setIdeas(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load ideas');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/projects`, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch projects');
      }

      const data = await response.json();
      setProjects(data.projects || []);
    } catch (err) {
      console.error('Failed to fetch projects:', err);
    }
  };

  const deleteIdea = async (ideaId: string) => {
    if (!window.confirm('Are you sure you want to delete this idea?')) return;

    try {
      const response = await fetch(`http://localhost:8000/api/ideas/${ideaId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete idea');
      }

      setIdeas(ideas.filter(idea => idea.id !== ideaId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete idea');
    }
  };

  const getFilteredIdeas = () => {
    return ideas.filter(idea => {
      // Status filter
      if (statusFilter !== 'all' && idea.status !== statusFilter) return false;
      
      // Level filter (company vs project)
      if (levelFilter === 'company' && idea.project_id) return false;
      if (levelFilter === 'project' && !idea.project_id) return false;
      
      // Project filter
      if (selectedProject !== 'all' && idea.project_id !== selectedProject) return false;
      
      // Search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          idea.title.toLowerCase().includes(query) ||
          idea.initial_description.toLowerCase().includes(query) ||
          (idea.refined_description || '').toLowerCase().includes(query)
        );
      }
      
      return true;
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'default';
      case 'refining': return 'info';
      case 'validated': return 'success';
      case 'rejected': return 'error';
      case 'converted': return 'primary';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'validated': return <ValidatedIcon />;
      case 'rejected': return <RejectedIcon />;
      case 'converted': return <TaskIcon />;
      default: return <IdeaIcon />;
    }
  };

  const getStatusStats = () => {
    const stats = {
      total: ideas.length,
      draft: ideas.filter(i => i.status === 'draft').length,
      refining: ideas.filter(i => i.status === 'refining').length,
      validated: ideas.filter(i => i.status === 'validated').length,
      rejected: ideas.filter(i => i.status === 'rejected').length,
      converted: ideas.filter(i => i.status === 'converted').length
    };
    return stats;
  };

  const stats = getStatusStats();
  const filteredIdeas = getFilteredIdeas();

  const renderIdeaCard = (idea: Idea) => {
    const project = projects.find(p => p.id === idea.project_id);
    
    return (
      <Card key={idea.id} className="idea-card" elevation={2}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
            <Typography variant="h6" component="h2" sx={{ flex: 1 }}>
              {idea.title}
            </Typography>
            <Chip
              size="small"
              icon={idea.project_id ? <ProjectIcon /> : <CompanyIcon />}
              label={idea.project_id ? project?.name || 'Project' : 'Company'}
              variant="outlined"
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {idea.refined_description || idea.initial_description}
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <Chip
              label={idea.status}
              color={getStatusColor(idea.status)}
              icon={getStatusIcon(idea.status)}
              size="small"
            />
            {idea.validation_score !== undefined && (
              <Chip
                label={`${(idea.validation_score * 100).toFixed(0)}%`}
                color="primary"
                icon={<ScoreIcon />}
                size="small"
                variant="outlined"
              />
            )}
            <Chip
              label={new Date(idea.created_at).toLocaleDateString()}
              size="small"
              variant="outlined"
            />
          </Box>
          
          {idea.conversation_history && idea.conversation_history.length > 0 && (
            <Typography variant="caption" color="text.secondary">
              {idea.conversation_history.length} messages in conversation
            </Typography>
          )}
        </CardContent>
        
        <CardActions sx={{ justifyContent: 'space-between' }}>
          <Button
            size="small"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/ideas/${idea.id}`)}
          >
            {idea.status === 'converted' ? 'View' : 'Continue'}
          </Button>
          
          {idea.status !== 'converted' && (
            <Tooltip title="Delete Idea">
              <IconButton
                size="small"
                color="error"
                onClick={() => deleteIdea(idea.id)}
              >
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          )}
        </CardActions>
      </Card>
    );
  };

  const renderIdeaListItem = (idea: Idea) => {
    const project = projects.find(p => p.id === idea.project_id);
    
    return (
      <Paper key={idea.id} sx={{ p: 2, mb: 1 }} elevation={1}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Typography variant="h6" component="span">
                {idea.title}
              </Typography>
              <Chip
                label={idea.status}
                color={getStatusColor(idea.status)}
                icon={getStatusIcon(idea.status)}
                size="small"
              />
              {idea.validation_score !== undefined && (
                <Chip
                  label={`${(idea.validation_score * 100).toFixed(0)}%`}
                  color="primary"
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
            <Typography variant="body2" color="text.secondary">
              {idea.refined_description || idea.initial_description}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {idea.project_id ? project?.name || 'Project' : 'Company Level'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Created {new Date(idea.created_at).toLocaleDateString()}
              </Typography>
              {idea.conversation_history && idea.conversation_history.length > 0 && (
                <Typography variant="caption" color="text.secondary">
                  {idea.conversation_history.length} messages
                </Typography>
              )}
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<EditIcon />}
              onClick={() => navigate(`/ideas/${idea.id}`)}
            >
              {idea.status === 'converted' ? 'View' : 'Continue'}
            </Button>
            {idea.status !== 'converted' && (
              <IconButton
                size="small"
                color="error"
                onClick={() => deleteIdea(idea.id)}
              >
                <DeleteIcon />
              </IconButton>
            )}
          </Box>
        </Box>
      </Paper>
    );
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box className="idea-board-container">
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Idea Board
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Capture, refine, validate, and convert your ideas into actionable tasks
        </Typography>
      </Box>

      {/* Stats */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
        <Paper sx={{ p: 2, textAlign: 'center', flex: '1 1 180px' }}>
          <Typography variant="h4">{stats.total}</Typography>
          <Typography variant="body2" color="text.secondary">Total Ideas</Typography>
        </Paper>
        <Paper sx={{ p: 2, textAlign: 'center', flex: '1 1 180px' }}>
          <Typography variant="h4" color="text.secondary">{stats.draft}</Typography>
          <Typography variant="body2" color="text.secondary">Draft</Typography>
        </Paper>
        <Paper sx={{ p: 2, textAlign: 'center', flex: '1 1 180px' }}>
          <Typography variant="h4" color="info.main">{stats.refining}</Typography>
          <Typography variant="body2" color="text.secondary">Refining</Typography>
        </Paper>
        <Paper sx={{ p: 2, textAlign: 'center', flex: '1 1 180px' }}>
          <Typography variant="h4" color="success.main">{stats.validated}</Typography>
          <Typography variant="body2" color="text.secondary">Validated</Typography>
        </Paper>
        <Paper sx={{ p: 2, textAlign: 'center', flex: '1 1 180px' }}>
          <Typography variant="h4" color="primary.main">{stats.converted}</Typography>
          <Typography variant="body2" color="text.secondary">Converted</Typography>
        </Paper>
      </Box>

      {/* Filters and Actions */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField
            sx={{ flex: '1 1 300px' }}
            size="small"
            placeholder="Search ideas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <FilterIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
          />
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              label="Status"
            >
              <MenuItem value="all">All Status</MenuItem>
              <MenuItem value="draft">Draft</MenuItem>
              <MenuItem value="refining">Refining</MenuItem>
              <MenuItem value="validated">Validated</MenuItem>
              <MenuItem value="rejected">Rejected</MenuItem>
              <MenuItem value="converted">Converted</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Level</InputLabel>
            <Select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              label="Level"
            >
              <MenuItem value="all">All Levels</MenuItem>
              <MenuItem value="company">Company</MenuItem>
              <MenuItem value="project">Project</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Project</InputLabel>
            <Select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              label="Project"
              disabled={levelFilter === 'company'}
            >
              <MenuItem value="all">All Projects</MenuItem>
              {projects.map(project => (
                <MenuItem key={project.id} value={project.id}>
                  {project.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            size="small"
          >
            <ToggleButton value="grid">
              <GridViewIcon />
            </ToggleButton>
            <ToggleButton value="list">
              <ListViewIcon />
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Paper>

      {/* Ideas Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {filteredIdeas.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <IdeaIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {ideas.length === 0 ? 'No ideas yet' : 'No ideas match your filters'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {ideas.length === 0 
              ? 'Start by creating your first idea and let AI help you refine it'
              : 'Try adjusting your filters to see more ideas'}
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/ideas/new')}
          >
            Create New Idea
          </Button>
        </Paper>
      ) : viewMode === 'grid' ? (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: 2 }}>
          {filteredIdeas.map(idea => renderIdeaCard(idea))}
        </Box>
      ) : (
        <Box>
          {filteredIdeas.map(idea => renderIdeaListItem(idea))}
        </Box>
      )}

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add idea"
        sx={{ position: 'fixed', bottom: 24, right: 24 }}
        onClick={() => navigate('/ideas/new')}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};

export default IdeaBoard;