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
  ArrowBack as BackIcon,
  TrendingUp as ScoreIcon
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
        className={`message-wrapper ${message.role}`}
      >
        <Box className="message-content">
          <Avatar className={`message-avatar ${message.role}`}>
            {isUser ? <PersonIcon /> : <BotIcon />}
          </Avatar>
          
          <Box className={`message-bubble ${message.role}`}>
            <Typography variant="body1" className="message-text">
              {message.content}
            </Typography>
            
            {message.questions && message.questions.length > 0 && (
              <Box className="questions-section">
                <Typography variant="caption" className="questions-title">
                  <IdeaIcon fontSize="small" />
                  Questions to consider:
                </Typography>
                <Box>
                  {message.questions.map((question, idx) => (
                    <Box 
                      key={idx} 
                      className="question-item"
                      onClick={() => setInputMessage(question)}
                    >
                      <Typography variant="body2">
                        {question}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
            
            <Typography variant="caption" className="message-timestamp">
              {new Date(message.timestamp).toLocaleTimeString()}
            </Typography>
          </Box>
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
    <Box className={`idea-assistant-container ${idea?.status || ''}`}>
      {/* Header */}
      <Paper elevation={0} className="idea-header">
        <Box className="idea-header-content">
          <Box className="idea-header-left">
            <IconButton 
              onClick={() => navigate('/ideas')}
              sx={{ color: 'white', bgcolor: 'rgba(255,255,255,0.1)', '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' } }}
            >
              <BackIcon />
            </IconButton>
            
            {idea && (
              <>
                <Typography variant="h5" className="idea-header-title">{idea.title}</Typography>
                <Chip
                  label={idea.status}
                  icon={getStatusIcon(idea.status)}
                  size="small"
                  className="idea-status-badge"
                  sx={{ color: 'white' }}
                />
                {idea.validation_score !== undefined && (
                  <Chip
                    label={`${(idea.validation_score * 100).toFixed(0)}%`}
                    icon={<ScoreIcon />}
                    size="small"
                    className="idea-status-badge"
                    sx={{ color: 'white' }}
                  />
                )}
                <Chip
                  label={idea.project_id ? 'Project' : 'Company'}
                  icon={idea.project_id ? <ProjectIcon /> : <CompanyIcon />}
                  size="small"
                  className="idea-status-badge"
                  sx={{ color: 'white' }}
                />
              </>
            )}
          </Box>
          
          {idea && idea.status !== 'converted' && (
            <Box className="idea-header-actions">
              {idea.status === 'draft' || idea.status === 'refining' ? (
                <Button
                  variant="contained"
                  onClick={validateIdea}
                  disabled={processingAction !== null}
                  startIcon={<CheckIcon />}
                  sx={{ 
                    bgcolor: 'white', 
                    color: '#667eea',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' },
                    fontWeight: 600
                  }}
                >
                  Validate Idea
                </Button>
              ) : idea.status === 'validated' ? (
                <Button
                  variant="contained"
                  onClick={convertToTasks}
                  disabled={processingAction !== null}
                  startIcon={<TaskIcon />}
                  sx={{ 
                    bgcolor: 'white', 
                    color: '#10b981',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' },
                    fontWeight: 600
                  }}
                >
                  Convert to Tasks
                </Button>
              ) : null}
              
              <Tooltip title="Delete Idea">
                <IconButton
                  onClick={deleteIdea}
                  disabled={idea.status === 'converted'}
                  sx={{ 
                    color: 'white', 
                    bgcolor: 'rgba(239,68,68,0.2)',
                    '&:hover': { bgcolor: 'rgba(239,68,68,0.3)' }
                  }}
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            </Box>
          )}
        </Box>
      </Paper>

      {/* Chat Container */}
      <Box className="chat-container">
        <Box className="chat-messages">
          {messages.length === 0 && idea && (
            <Card className="welcome-card fade-in" elevation={0}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Welcome to the Idea Assistant! 🚀
                </Typography>
                <Typography variant="body2" className="idea-description">
                  {idea.initial_description}
                </Typography>
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Let's work together to develop this into a clear, actionable plan. Feel free to share more details or answer any questions I have.
                </Typography>
              </CardContent>
            </Card>
          )}
        
        {messages.map((message, index) => renderMessage(message, index))}
        
          {loading && (
            <Box className="typing-indicator">
              <Box className="typing-dots">
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </Box>
              <Typography variant="body2">
                AI is thinking...
              </Typography>
            </Box>
          )}
        
          {processingAction && (
            <Alert 
              severity="info" 
              className="processing-alert slide-up"
              icon={<CircularProgress size={20} />}
            >
              {processingAction === 'validating' ? 'Validating your idea...' : 'Converting to tasks...'}
            </Alert>
          )}
        
          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        {idea && idea.status !== 'converted' && (
          <Box className="input-area">
            <Box className="input-wrapper">
              <TextField
                fullWidth
                placeholder="Type your message here..."
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
                className="message-input"
                InputProps={{
                  disableUnderline: true,
                  sx: { fontSize: '16px' }
                }}
                variant="standard"
              />
              <Button
                variant="contained"
                onClick={sendMessage}
                disabled={!inputMessage.trim() || loading || processingAction !== null}
                className="send-button"
                endIcon={<SendIcon />}
              >
                Send
              </Button>
            </Box>
          </Box>
        )}
      </Box>

      {/* New Idea Dialog */}
      <Dialog open={showNewIdeaDialog} onClose={() => navigate('/ideas')} maxWidth="sm" fullWidth className="idea-dialog">
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
            <Alert severity="info" className="create-idea-info" icon={<IdeaIcon />}>
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