import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  IconButton,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Card,
  CardContent,
  Stack,
  Avatar,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Task as TaskIcon,
  Lightbulb as IdeaIcon,
  Business as CompanyIcon,
  Folder as ProjectIcon,
  Delete as DeleteIcon,
  ArrowBack as BackIcon
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import './IdeaAssistant.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  questions?: string[];
}

interface Idea {
  id: string;
  title: string;
  initial_description: string;
  refined_description?: string;
  status: string;
  validation_score?: number;
  validation_reasons?: any;
  conversation_history: Message[];
  project_id?: string;
  created_at: string;
  updated_at: string;
}

const IdeaAssistant: React.FC = () => {
  const { ideaId } = useParams<{ ideaId?: string }>();
  const navigate = useNavigate();
  const { session } = useSupabaseAuth();
  const [idea, setIdea] = useState<Idea | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [processingAction, setProcessingAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showNewIdeaDialog, setShowNewIdeaDialog] = useState(!ideaId);
  const [newIdeaTitle, setNewIdeaTitle] = useState('');
  const [newIdeaDescription, setNewIdeaDescription] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchIdea = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/ideas/${ideaId}`, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch idea');
      }

      const data = await response.json();
      setIdea(data);
      setMessages(data.conversation_history || []);
      setProjectId(data.project_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load idea');
    } finally {
      setLoading(false);
    }
  }, [ideaId, session]);

  useEffect(() => {
    if (ideaId) {
      fetchIdea();
    }
  }, [ideaId, fetchIdea]);

  const createIdea = async () => {
    if (!newIdeaTitle.trim() || !newIdeaDescription.trim()) {
      setError('Please provide both title and description');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/ideas`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: newIdeaTitle,
          initial_description: newIdeaDescription,
          project_id: projectId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create idea');
      }

      const newIdea = await response.json();
      navigate(`/ideas/${newIdea.id}`);
      setShowNewIdeaDialog(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create idea');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !ideaId) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages([...messages, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/api/ideas/${ideaId}/refine`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: inputMessage
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        questions: data.questions
      };

      setMessages([...messages, userMessage, assistantMessage]);
      
      // Update idea if refined description is provided
      if (data.refined_description) {
        setIdea(prev => prev ? { ...prev, refined_description: data.refined_description } : null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  const validateIdea = async () => {
    if (!ideaId) return;
    
    setProcessingAction('validating');
    try {
      const response = await fetch(`http://localhost:8000/api/ideas/${ideaId}/validate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to validate idea');
      }

      const data = await response.json();
      
      // Refresh idea to get updated status
      await fetchIdea();
      
      // Add validation result to messages
      const validationMessage: Message = {
        role: 'assistant',
        content: `Validation Complete!\n\nScore: ${(data.validation_score * 100).toFixed(0)}%\nRecommendation: ${data.recommendation}\n\nReasons:\n${Object.entries(data.validation_reasons).map(([key, value]) => `• ${key}: ${value}`).join('\n')}`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, validationMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to validate idea');
    } finally {
      setProcessingAction(null);
    }
  };

  const convertToTasks = async () => {
    if (!ideaId) return;
    
    setProcessingAction('converting');
    try {
      const response = await fetch(`http://localhost:8000/api/ideas/${ideaId}/convert`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to convert to tasks');
      }

      const data = await response.json();
      
      // Refresh idea to get updated status
      await fetchIdea();
      
      // Add conversion result to messages
      const conversionMessage: Message = {
        role: 'assistant',
        content: `Successfully created ${data.tasks_created} tasks!\n\nTasks:\n${data.tasks.map((task: any, idx: number) => `${idx + 1}. ${task.title} (${task.priority} priority, ${task.effort})`).join('\n')}`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, conversionMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to convert to tasks');
    } finally {
      setProcessingAction(null);
    }
  };

  const deleteIdea = async () => {
    if (!ideaId || !window.confirm('Are you sure you want to delete this idea?')) return;
    
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

      navigate('/ideas');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete idea');
    }
  };

  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === 'user';
    
    return (
      <Box
        key={index}
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            maxWidth: '70%',
            flexDirection: isUser ? 'row-reverse' : 'row'
          }}
        >
          <Avatar
            sx={{
              bgcolor: isUser ? 'primary.main' : 'secondary.main',
              mx: 1
            }}
          >
            {isUser ? <PersonIcon /> : <BotIcon />}
          </Avatar>
          
          <Paper
            elevation={1}
            sx={{
              p: 2,
              bgcolor: isUser ? 'primary.light' : 'background.paper',
              color: isUser ? 'primary.contrastText' : 'text.primary',
              borderRadius: 2
            }}
          >
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {message.content}
            </Typography>
            
            {message.questions && message.questions.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
                  Questions to consider:
                </Typography>
                <List dense>
                  {message.questions.map((question, idx) => (
                    <ListItem key={idx}>
                      <ListItemText
                        primary={question}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
            
            <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.7 }}>
              {new Date(message.timestamp).toLocaleTimeString()}
            </Typography>
          </Paper>
        </Box>
      </Box>
    );
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
      case 'validated': return <CheckIcon />;
      case 'rejected': return <CancelIcon />;
      case 'converted': return <TaskIcon />;
      default: return <IdeaIcon />;
    }
  };

  if (loading && !idea) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box className="idea-assistant-container">
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton onClick={() => navigate('/ideas')}>
              <BackIcon />
            </IconButton>
            
            {idea && (
              <>
                <Typography variant="h5">{idea.title}</Typography>
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
                    variant="outlined"
                    size="small"
                  />
                )}
                <Chip
                  label={idea.project_id ? 'Project' : 'Company'}
                  icon={idea.project_id ? <ProjectIcon /> : <CompanyIcon />}
                  size="small"
                  variant="outlined"
                />
              </>
            )}
          </Box>
          
          {idea && idea.status !== 'converted' && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              {idea.status === 'draft' || idea.status === 'refining' ? (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={validateIdea}
                  disabled={processingAction !== null}
                  startIcon={<CheckIcon />}
                >
                  Validate Idea
                </Button>
              ) : idea.status === 'validated' ? (
                <Button
                  variant="contained"
                  color="success"
                  onClick={convertToTasks}
                  disabled={processingAction !== null}
                  startIcon={<TaskIcon />}
                >
                  Convert to Tasks
                </Button>
              ) : null}
              
              <Tooltip title="Delete Idea">
                <IconButton
                  color="error"
                  onClick={deleteIdea}
                  disabled={idea.status === 'converted'}
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            </Box>
          )}
        </Box>
      </Paper>

      {/* Chat Messages */}
      <Paper elevation={1} sx={{ flex: 1, p: 2, mb: 2, minHeight: '400px', maxHeight: '600px', overflow: 'auto' }}>
        {messages.length === 0 && idea && (
          <Card sx={{ mb: 2, bgcolor: 'info.light' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Welcome to the Idea Assistant!
              </Typography>
              <Typography variant="body2">
                I'm here to help you refine your idea: "{idea.initial_description}"
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Let's work together to develop this into a clear, actionable plan. Feel free to share more details or answer any questions I have.
              </Typography>
            </CardContent>
          </Card>
        )}
        
        {messages.map((message, index) => renderMessage(message, index))}
        
        {loading && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
            <CircularProgress size={20} />
            <Typography variant="body2" color="text.secondary">
              AI is thinking...
            </Typography>
          </Box>
        )}
        
        {processingAction && (
          <Alert severity="info" sx={{ mt: 2 }}>
            {processingAction === 'validating' ? 'Validating your idea...' : 'Converting to tasks...'}
          </Alert>
        )}
        
        <div ref={messagesEndRef} />
      </Paper>

      {/* Input Area */}
      {idea && idea.status !== 'converted' && (
        <Paper elevation={1} sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Type your message..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              disabled={loading || processingAction !== null}
              multiline
              maxRows={4}
            />
            <Button
              variant="contained"
              color="primary"
              onClick={sendMessage}
              disabled={!inputMessage.trim() || loading || processingAction !== null}
              sx={{ minWidth: '120px' }}
              endIcon={<SendIcon />}
            >
              Send
            </Button>
          </Box>
        </Paper>
      )}

      {/* New Idea Dialog */}
      <Dialog open={showNewIdeaDialog} onClose={() => navigate('/ideas')} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Idea</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="Idea Title"
              value={newIdeaTitle}
              onChange={(e) => setNewIdeaTitle(e.target.value)}
              placeholder="Give your idea a clear, concise title"
            />
            <TextField
              fullWidth
              label="Initial Description"
              value={newIdeaDescription}
              onChange={(e) => setNewIdeaDescription(e.target.value)}
              placeholder="Describe your idea in detail. What problem does it solve? What's your vision?"
              multiline
              rows={4}
            />
            <Alert severity="info">
              The AI assistant will help you refine this idea through conversation, validate its feasibility, and break it down into actionable tasks.
            </Alert>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => navigate('/ideas')}>Cancel</Button>
          <Button
            variant="contained"
            onClick={createIdea}
            disabled={!newIdeaTitle.trim() || !newIdeaDescription.trim() || loading}
          >
            Create Idea
          </Button>
        </DialogActions>
      </Dialog>

      {/* Error Snackbar */}
      {error && (
        <Alert
          severity="error"
          onClose={() => setError(null)}
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
        >
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default IdeaAssistant;