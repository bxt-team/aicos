import React, { useState, useEffect } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Paper,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Radio,
  RadioGroup,
  Badge,
  Tooltip
} from '@mui/material';
import {
  Create as CreateIcon,
  Twitter as TwitterIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Poll as PollIcon,
  Link as LinkIcon,
  Schedule as ScheduleIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import axios from 'axios';

interface XPost {
  type: 'single' | 'thread' | 'poll';
  content: string;
  thread_content?: string[];
  poll_options?: string[];
  character_count: number;
  hashtags: string[];
  visual_prompt?: string;
  best_time?: string;
  expected_engagement?: string;
  period: number;
  call_to_action?: string;
  activity_id?: string;
}

interface ApprovalResult {
  post_index: number;
  approval_status: string;
  quality_score: number;
  feedback: string;
  suggestions: string[];
}

const XPostManager: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [period, setPeriod] = useState(1);
  const [postType, setPostType] = useState<'single' | 'thread' | 'poll' | 'mixed'>('mixed');
  const [postCount, setPostCount] = useState(5);
  const [posts, setPosts] = useState<XPost[]>([]);
  const [editingPost, setEditingPost] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [approvalResults, setApprovalResults] = useState<ApprovalResult[]>([]);
  const [hasStrategy, setHasStrategy] = useState(false);
  const [previewPost, setPreviewPost] = useState<XPost | null>(null);

  useEffect(() => {
    checkStrategy();
  }, []);

  const checkStrategy = async () => {
    try {
      const response = await axios.get('/api/x/strategy/latest');
      setHasStrategy(response.data.success && !response.data.strategy.error);
    } catch {
      setHasStrategy(false);
    }
  };

  const handleGeneratePosts = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/x/posts/generate', {
        period,
        post_type: postType,
        count: postCount,
        use_latest_strategy: true
      });

      if (response.data.success) {
        const generatedPosts = response.data.posts.filter((p: any) => p.type !== 'ai_generated');
        setPosts(generatedPosts);
        setActiveStep(1);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate posts');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitForApproval = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/x/posts/approve', {
        posts,
        requester: 'user'
      });

      if (response.data.success) {
        setApprovalResults(response.data.approval_request.review_results);
        setActiveStep(2);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit for approval');
    } finally {
      setLoading(false);
    }
  };

  const handleEditPost = (index: number) => {
    setEditingPost(index);
  };

  const handleSavePost = (index: number, updatedPost: XPost) => {
    const newPosts = [...posts];
    newPosts[index] = updatedPost;
    setPosts(newPosts);
    setEditingPost(null);
  };

  const handleDeletePost = (index: number) => {
    setPosts(posts.filter((_, i) => i !== index));
  };

  const calculateCharacterCount = (content: string): number => {
    return content.length;
  };

  const getStatusColor = (status: string): 'success' | 'warning' | 'error' => {
    switch (status) {
      case 'approved':
        return 'success';
      case 'needs_revision':
        return 'warning';
      case 'rejected':
        return 'error';
      default:
        return 'warning';
    }
  };

  const renderPostPreview = (post: XPost) => (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {post.type === 'thread' && <LinkIcon color="primary" />}
            {post.type === 'poll' && <PollIcon color="secondary" />}
            <Chip label={`Cycle ${post.period}`} size="small" color="primary" />
            <Chip label={post.type} size="small" variant="outlined" />
          </Box>
          <Typography variant="caption" color={post.character_count > 280 ? 'error' : 'text.secondary'}>
            {post.character_count}/280
          </Typography>
        </Box>

        <Typography variant="body1" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
          {post.content}
        </Typography>

        {post.thread_content && post.thread_content.length > 0 && (
          <Box sx={{ mb: 2, pl: 2, borderLeft: '3px solid', borderColor: 'primary.main' }}>
            <Typography variant="caption" color="text.secondary">Thread continues:</Typography>
            {post.thread_content.slice(0, 2).map((tweet, idx) => (
              <Typography key={idx} variant="body2" sx={{ mt: 1 }}>
                {idx + 2}/ {tweet.substring(0, 100)}...
              </Typography>
            ))}
            {post.thread_content.length > 2 && (
              <Typography variant="caption" color="text.secondary">
                +{post.thread_content.length - 2} more tweets
              </Typography>
            )}
          </Box>
        )}

        {post.poll_options && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary">Poll Options:</Typography>
            <List dense>
              {post.poll_options.map((option, idx) => (
                <ListItem key={idx}>
                  <ListItemText primary={`${idx + 1}. ${option}`} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {post.hashtags.map((tag) => (
            <Chip key={tag} label={tag} size="small" color="primary" variant="outlined" />
          ))}
        </Box>

        {post.best_time && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScheduleIcon fontSize="small" color="action" />
            <Typography variant="caption" color="text.secondary">
              Best time: {post.best_time}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CreateIcon /> X Post Manager
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Generate, review, and approve X posts for publishing
        </Typography>

        {!hasStrategy && (
          <Alert severity="info" sx={{ mb: 2 }}>
            No strategy found. Create a strategy first for optimized post generation.
          </Alert>
        )}
      </Paper>

      <Stepper activeStep={activeStep} orientation="vertical">
        <Step>
          <StepLabel>Generate Posts</StepLabel>
          <StepContent>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid size={{ xs: 12, sm: 4 }}>
                <FormControl fullWidth>
                  <InputLabel>Period</InputLabel>
                  <Select
                    value={period}
                    onChange={(e) => setPeriod(Number(e.target.value))}
                    label="Period"
                  >
                    {[1, 2, 3, 4, 5, 6, 7].map((p) => (
                      <MenuItem key={p} value={p}>
                        Cycle {p}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid size={{ xs: 12, sm: 4 }}>
                <FormControl fullWidth>
                  <InputLabel>Post Type</InputLabel>
                  <Select
                    value={postType}
                    onChange={(e) => setPostType(e.target.value as any)}
                    label="Post Type"
                  >
                    <MenuItem value="mixed">Mixed</MenuItem>
                    <MenuItem value="single">Single Tweets</MenuItem>
                    <MenuItem value="thread">Threads</MenuItem>
                    <MenuItem value="poll">Polls</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField
                  fullWidth
                  type="number"
                  label="Number of Posts"
                  value={postCount}
                  onChange={(e) => setPostCount(Number(e.target.value))}
                  inputProps={{ min: 1, max: 10 }}
                />
              </Grid>
            </Grid>

            <Box sx={{ mb: 2 }}>
              <Button
                variant="contained"
                onClick={handleGeneratePosts}
                disabled={loading || !hasStrategy}
                startIcon={loading ? <CircularProgress size={20} /> : <TwitterIcon />}
              >
                {loading ? 'Generating...' : 'Generate Posts'}
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </StepContent>
        </Step>

        <Step>
          <StepLabel>Review & Edit</StepLabel>
          <StepContent>
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Generated Posts ({posts.length})
              </Typography>
              
              {posts.map((post, index) => (
                <Box key={index}>
                  {editingPost === index ? (
                    <Card sx={{ mb: 2, p: 2 }}>
                      <TextField
                        fullWidth
                        multiline
                        rows={4}
                        value={post.content}
                        onChange={(e) => {
                          const updatedPost = { ...post, content: e.target.value, character_count: e.target.value.length };
                          handleSavePost(index, updatedPost);
                        }}
                        sx={{ mb: 2 }}
                      />
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button onClick={() => handleSavePost(index, post)}>Save</Button>
                        <Button onClick={() => setEditingPost(null)}>Cancel</Button>
                      </Box>
                    </Card>
                  ) : (
                    <Box sx={{ position: 'relative' }}>
                      {renderPostPreview(post)}
                      <Box sx={{ position: 'absolute', top: 8, right: 8 }}>
                        <IconButton size="small" onClick={() => handleEditPost(index)}>
                          <EditIcon />
                        </IconButton>
                        <IconButton size="small" onClick={() => setPreviewPost(post)}>
                          <VisibilityIcon />
                        </IconButton>
                        <IconButton size="small" onClick={() => handleDeletePost(index)} color="error">
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    </Box>
                  )}
                </Box>
              ))}

              <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleSubmitForApproval}
                  disabled={posts.length === 0 || loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <CheckCircleIcon />}
                >
                  Submit for Approval
                </Button>
                <Button onClick={() => setActiveStep(0)}>
                  Back
                </Button>
              </Box>
            </Box>
          </StepContent>
        </Step>

        <Step>
          <StepLabel>Approval Results</StepLabel>
          <StepContent>
            <Box>
              <Typography variant="h6" gutterBottom>
                Approval Results
              </Typography>
              
              {approvalResults.map((result, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Chip 
                        label={result.approval_status.replace('_', ' ')}
                        color={getStatusColor(result.approval_status)}
                        icon={result.approval_status === 'approved' ? <CheckCircleIcon /> : <CancelIcon />}
                      />
                      <Typography variant="body2">
                        Quality Score: {result.quality_score}/10
                      </Typography>
                    </Box>
                    
                    <Typography variant="body2" paragraph>
                      {result.feedback}
                    </Typography>
                    
                    {result.suggestions.length > 0 && (
                      <>
                        <Typography variant="subtitle2" gutterBottom>
                          Suggestions:
                        </Typography>
                        <List dense>
                          {result.suggestions.map((suggestion, idx) => (
                            <ListItem key={idx}>
                              <ListItemText primary={suggestion} />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}
                  </CardContent>
                </Card>
              ))}

              <Box sx={{ mt: 3 }}>
                <Button
                  variant="contained"
                  onClick={() => {
                    // Move to schedule step
                    window.location.hash = '#schedule';
                  }}
                  disabled={!approvalResults.some(r => r.approval_status === 'approved')}
                >
                  Schedule Approved Posts
                </Button>
                <Button onClick={() => setActiveStep(1)} sx={{ ml: 2 }}>
                  Back to Edit
                </Button>
              </Box>
            </Box>
          </StepContent>
        </Step>
      </Stepper>

      {/* Preview Dialog */}
      <Dialog
        open={Boolean(previewPost)}
        onClose={() => setPreviewPost(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Tweet Preview</DialogTitle>
        <DialogContent>
          {previewPost && (
            <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <TwitterIcon color="primary" />
                <Typography variant="subtitle2">@7cycles</Typography>
                <Typography variant="caption" color="text.secondary">• now</Typography>
              </Box>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {previewPost.content}
              </Typography>
              {previewPost.hashtags.length > 0 && (
                <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                  {previewPost.hashtags.join(' ')}
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewPost(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default XPostManager;