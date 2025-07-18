import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Card,
  CardContent,
  CardActions,
  Chip,
  CircularProgress,
  Alert,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  Switch,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  Divider,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Create as CreateIcon,
  ThumbUp as ApproveIcon,
  Schedule as ScheduleIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as PreviewIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { SelectChangeEvent } from '@mui/material/Select';
import axios from 'axios';

interface ThreadsPost {
  id?: string;
  content: string;
  hashtags: string[];
  period: number;
  visual_prompt?: string;
  post_type: string;
  call_to_action: string;
  created_at?: string;
  status?: string;
}

interface ApprovalRequest {
  id: string;
  posts: ThreadsPost[];
  assessment: {
    overall_quality: string;
    posts_assessment: Array<{
      post_index: number;
      quality_score: number;
      approval_recommendation: string;
      issues: string[];
      recommendations: string[];
    }>;
  };
  status: string;
}

const periods = [
  { value: 1, name: 'IMAGE', color: '#DAA520' },
  { value: 2, name: 'VERÄNDERUNG', color: '#FF6B6B' },
  { value: 3, name: 'ENERGIE', color: '#4ECDC4' },
  { value: 4, name: 'KREATIVITÄT', color: '#9B59B6' },
  { value: 5, name: 'ERFOLG', color: '#F39C12' },
  { value: 6, name: 'ENTSPANNUNG', color: '#3498DB' },
  { value: 7, name: 'UMSICHT', color: '#2ECC71' },
];

const ThreadsPostManager: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [posts, setPosts] = useState<ThreadsPost[]>([]);
  const [allPosts, setAllPosts] = useState<ThreadsPost[]>([]);
  const [showAllPosts, setShowAllPosts] = useState(false);
  const [approvalResult, setApprovalResult] = useState<any>(null);
  const [activeStep, setActiveStep] = useState(0);
  
  // Generation parameters
  const [count, setCount] = useState(5);
  const [selectedPeriod, setSelectedPeriod] = useState<number | ''>('');
  const [theme, setTheme] = useState('');
  const [includeAffirmations, setIncludeAffirmations] = useState(true);
  const [includeActivities, setIncludeActivities] = useState(true);
  
  // Edit dialog
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingPost, setEditingPost] = useState<ThreadsPost | null>(null);
  const [editingIndex, setEditingIndex] = useState<number>(-1);

  const steps = ['Generate Posts', 'Review & Edit', 'Request Approval', 'Schedule'];

  useEffect(() => {
    if (showAllPosts) {
      loadAllPosts();
    }
  }, [showAllPosts]);

  const loadAllPosts = async () => {
    try {
      const response = await axios.get('/api/threads/posts/unapproved');
      setAllPosts(response.data.posts);
    } catch (err) {
      console.error('Failed to load posts:', err);
    }
  };

  const handleDeletePost = async (postId: string) => {
    if (!window.confirm('Are you sure you want to delete this post?')) return;
    
    try {
      await axios.delete(`/api/threads/posts/${postId}`);
      setSuccess('Post deleted successfully');
      loadAllPosts();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete post');
    }
  };

  const handleApprovePost = async (post: ThreadsPost) => {
    try {
      // Create a single-post approval request
      const response = await axios.post('/api/threads/posts/approve', {
        posts: [post]
      });
      
      if (response.data.success && response.data.decision_result?.approval_request?.status === 'approved') {
        setSuccess('Post approved successfully');
        loadAllPosts();
      } else {
        setError('Post did not meet approval criteria');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to approve post');
    }
  };

  const generatePosts = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post('/api/threads/posts/generate', {
        count,
        period: selectedPeriod || undefined,
        theme: theme || undefined,
        include_affirmations: includeAffirmations,
        include_activities: includeActivities,
      });

      if (response.data.success) {
        setPosts(response.data.posts);
        setSuccess(`Generated ${response.data.count} posts successfully!`);
        setActiveStep(1);
      } else {
        throw new Error(response.data.error || 'Generation failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate posts');
    } finally {
      setLoading(false);
    }
  };

  const requestApproval = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post('/api/threads/posts/approve');

      if (response.data.success) {
        setApprovalResult(response.data);
        setSuccess('Approval request submitted successfully!');
        setActiveStep(2);
      } else {
        throw new Error(response.data.error || 'Approval request failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to request approval');
    } finally {
      setLoading(false);
    }
  };

  const handleEditPost = (post: ThreadsPost, index: number) => {
    setEditingPost({ ...post });
    setEditingIndex(index);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = () => {
    if (editingPost && editingIndex >= 0) {
      const newPosts = [...posts];
      newPosts[editingIndex] = editingPost;
      setPosts(newPosts);
      setEditDialogOpen(false);
      setEditingPost(null);
      setEditingIndex(-1);
    }
  };

  const handleDeleteGeneratedPost = (index: number) => {
    setPosts(posts.filter((_, i) => i !== index));
  };

  const proceedToSchedule = () => {
    setActiveStep(3);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Post Manager
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Generate, review, and approve Threads posts
          </Typography>
        </Box>
        <Button
          variant={showAllPosts ? 'contained' : 'outlined'}
          onClick={() => setShowAllPosts(!showAllPosts)}
        >
          {showAllPosts ? 'Hide All Posts' : 'Show All Posts'}
        </Button>
      </Box>

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {activeStep === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Generate New Posts
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  type="number"
                  label="Number of Posts"
                  value={count}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCount(parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 20 }}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Period (Optional)</InputLabel>
                  <Select
                    value={selectedPeriod}
                    onChange={(e: SelectChangeEvent<number | ''>) => setSelectedPeriod(e.target.value as number | '')}
                    label="Period (Optional)"
                  >
                    <MenuItem value="">All Periods</MenuItem>
                    {periods.map((period) => (
                      <MenuItem key={period.value} value={period.value}>
                        {period.value}. {period.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={12}>
                <TextField
                  fullWidth
                  label="Theme (Optional)"
                  value={theme}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTheme(e.target.value)}
                  placeholder="e.g., Morning motivation, Weekly reflection"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={includeAffirmations}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setIncludeAffirmations(e.target.checked)}
                    />
                  }
                  label="Include Affirmations"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={includeActivities}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setIncludeActivities(e.target.checked)}
                    />
                  }
                  label="Include Activities"
                />
              </Grid>
            </Grid>
          </CardContent>
          <CardActions>
            <Button
              startIcon={<CreateIcon />}
              onClick={generatePosts}
              variant="contained"
              disabled={loading}
            >
              {loading ? 'Generating...' : 'Generate Posts'}
            </Button>
          </CardActions>
        </Card>
      )}

      {activeStep === 1 && posts.length > 0 && (
        <>
          <Typography variant="h6" gutterBottom>
            Review Generated Posts
          </Typography>
          <Grid container spacing={2}>
            {posts.map((post, index) => {
              const period = periods.find(p => p.value === post.period);
              return (
                <Grid size={{ xs: 12, md: 6 }} key={index}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                        <Chip
                          label={`${period?.name} (${post.period})`}
                          size="small"
                          sx={{ bgcolor: period?.color, color: 'white' }}
                        />
                        <Chip
                          label={post.post_type}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                      <Typography variant="body1" paragraph>
                        {post.content}
                      </Typography>
                      <Box sx={{ mb: 2 }}>
                        {post.hashtags.map((tag, i) => (
                          <Chip
                            key={i}
                            label={tag}
                            size="small"
                            sx={{ m: 0.5 }}
                          />
                        ))}
                      </Box>
                      {post.call_to_action && (
                        <Typography variant="body2" color="primary" gutterBottom>
                          CTA: {post.call_to_action}
                        </Typography>
                      )}
                      {post.visual_prompt && (
                        <Typography variant="body2" color="text.secondary">
                          Visual: {post.visual_prompt}
                        </Typography>
                      )}
                    </CardContent>
                    <CardActions>
                      <IconButton
                        size="small"
                        onClick={() => handleEditPost(post, index)}
                        color="primary"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteGeneratedPost(index)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </CardActions>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={() => setActiveStep(0)}
            >
              Back to Generate
            </Button>
            <Button
              startIcon={<ApproveIcon />}
              onClick={requestApproval}
              variant="contained"
              disabled={loading || posts.length === 0}
            >
              {loading ? 'Requesting...' : 'Request Approval'}
            </Button>
          </Box>
        </>
      )}

      {activeStep === 2 && approvalResult && (
        <>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Approval Status
              </Typography>
              {approvalResult.telegram_simulation && (
                <>
                  <Alert 
                    severity={approvalResult.telegram_simulation.decision === 'approved' ? 'success' : 
                             approvalResult.telegram_simulation.decision === 'needs_revision' ? 'warning' : 'error'} 
                    sx={{ mb: 2 }}
                  >
                    Telegram Bot Decision: {approvalResult.telegram_simulation.decision}
                  </Alert>
                  
                  {approvalResult.telegram_simulation.assessment_summary && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Overall Quality: <strong>{approvalResult.telegram_simulation.assessment_summary.overall_quality}</strong>
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Average Score: <strong>{approvalResult.telegram_simulation.assessment_summary.average_score}/10</strong>
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                        <Chip 
                          icon={<CheckIcon />} 
                          label={`${approvalResult.telegram_simulation.assessment_summary.approved_posts} Approved`} 
                          color="success" 
                          size="small" 
                        />
                        <Chip 
                          icon={<EditIcon />} 
                          label={`${approvalResult.telegram_simulation.assessment_summary.revision_needed} Need Revision`} 
                          color="warning" 
                          size="small" 
                        />
                        <Chip 
                          icon={<CancelIcon />} 
                          label={`${approvalResult.telegram_simulation.assessment_summary.rejected_posts} Rejected`} 
                          color="error" 
                          size="small" 
                        />
                      </Box>
                    </Box>
                  )}
                  
                  <Typography variant="body2" color="text.secondary">
                    {approvalResult.telegram_simulation.notes}
                  </Typography>
                </>
              )}
              {approvalResult.decision_result && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body1" gutterBottom>
                    Status: {approvalResult.decision_result.approval_request.status}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {approvalResult.decision_result.message}
                  </Typography>
                </Box>
              )}
            </CardContent>
            <CardActions>
              {approvalResult.telegram_simulation?.decision === 'needs_revision' && (
                <Button
                  variant="outlined"
                  onClick={() => {
                    setActiveStep(1);
                    setApprovalResult(null);
                  }}
                  sx={{ mr: 1 }}
                >
                  Back to Edit Posts
                </Button>
              )}
              {approvalResult.telegram_simulation?.decision === 'rejected' && (
                <Button
                  variant="outlined"
                  onClick={() => {
                    setActiveStep(0);
                    setPosts([]);
                    setApprovalResult(null);
                  }}
                  sx={{ mr: 1 }}
                >
                  Generate New Posts
                </Button>
              )}
              <Button
                startIcon={<ScheduleIcon />}
                onClick={proceedToSchedule}
                variant="contained"
                disabled={approvalResult.decision_result?.approval_request?.status !== 'approved'}
              >
                Proceed to Schedule
              </Button>
            </CardActions>
          </Card>
          
          {/* Post Assessment Details */}
          {approvalResult.approval_request?.assessment?.posts_assessment && (
            <>
              <Typography variant="h6" gutterBottom>
                Post Assessment Details
              </Typography>
              <Grid container spacing={2}>
                {approvalResult.approval_request.assessment.posts_assessment.map((assessment: any, index: number) => (
                  <Grid size={{ xs: 12, md: 6 }} key={index}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Typography variant="subtitle1" fontWeight="bold">
                            Post {index + 1}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Chip 
                              label={`Score: ${assessment.quality_score}/10`} 
                              size="small"
                              color={assessment.quality_score >= 7 ? 'success' : assessment.quality_score >= 5 ? 'warning' : 'error'}
                            />
                            <Chip 
                              label={assessment.approval_recommendation} 
                              size="small"
                              variant="outlined"
                              color={assessment.approval_recommendation === 'approved' ? 'success' : 
                                     assessment.approval_recommendation === 'needs_revision' ? 'warning' : 'error'}
                            />
                          </Box>
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {assessment.content_preview}
                        </Typography>
                        
                        <Typography variant="body2" gutterBottom>
                          Engagement Potential: <strong>{assessment.engagement_potential}</strong>
                        </Typography>
                        
                        {assessment.issues && assessment.issues.length > 0 && (
                          <Box sx={{ mt: 1, mb: 1 }}>
                            <Typography variant="body2" color="error.main" gutterBottom>
                              Issues:
                            </Typography>
                            {assessment.issues.map((issue: string, i: number) => (
                              <Typography key={i} variant="body2" color="text.secondary" sx={{ pl: 2 }}>
                                • {issue}
                              </Typography>
                            ))}
                          </Box>
                        )}
                        
                        {assessment.recommendations && assessment.recommendations.length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2" color="primary.main" gutterBottom>
                              Recommendations:
                            </Typography>
                            {assessment.recommendations.map((rec: string, i: number) => (
                              <Typography key={i} variant="body2" color="text.secondary" sx={{ pl: 2 }}>
                                • {rec}
                              </Typography>
                            ))}
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </>
          )}
        </>
      )}

      {activeStep === 3 && (
        <Alert severity="success">
          Posts approved! Switch to the Schedule tab to schedule your posts.
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {success}
        </Alert>
      )}

      {/* All Posts Section */}
      {showAllPosts && (
        <>
          <Divider sx={{ my: 4 }} />
          <Typography variant="h6" gutterBottom>
            All Unapproved Posts
          </Typography>
          {allPosts.length === 0 ? (
            <Alert severity="info">No unapproved posts found</Alert>
          ) : (
            <Grid container spacing={2}>
              {allPosts.map((post) => {
                const period = periods.find(p => p.value === post.period);
                return (
                  <Grid size={{ xs: 12, md: 6 }} key={post.id}>
                    <Card>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Chip
                              label={`${period?.name} (${post.period})`}
                              size="small"
                              sx={{ bgcolor: period?.color, color: 'white' }}
                            />
                            <Chip
                              label={post.status || 'draft'}
                              size="small"
                              variant="outlined"
                              color={
                                post.status === 'needs_revision' ? 'warning' :
                                post.status === 'rejected' ? 'error' : 'default'
                              }
                            />
                          </Box>
                          <Chip
                            label={post.post_type}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                        <Typography variant="body1" paragraph>
                          {post.content}
                        </Typography>
                        <Box sx={{ mb: 2 }}>
                          {post.hashtags.map((tag, i) => (
                            <Chip
                              key={i}
                              label={tag}
                              size="small"
                              sx={{ m: 0.5 }}
                            />
                          ))}
                        </Box>
                        {post.call_to_action && (
                          <Typography variant="body2" color="primary" gutterBottom>
                            CTA: {post.call_to_action}
                          </Typography>
                        )}
                        {post.visual_prompt && (
                          <Typography variant="body2" color="text.secondary">
                            Visual: {post.visual_prompt}
                          </Typography>
                        )}
                      </CardContent>
                      <CardActions>
                        <IconButton
                          size="small"
                          onClick={() => handleEditPost(post, -1)}
                          color="primary"
                          title="Edit"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleApprovePost(post)}
                          color="success"
                          title="Quick Approve"
                        >
                          <ApproveIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeletePost(post.id!)}
                          color="error"
                          title="Delete"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </CardActions>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          )}
        </>
      )}

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Post</DialogTitle>
        <DialogContent>
          {editingPost && (
            <Box sx={{ pt: 2 }}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Content"
                value={editingPost.content}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditingPost({ ...editingPost, content: e.target.value })}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Hashtags (comma separated)"
                value={editingPost.hashtags.join(', ')}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditingPost({
                  ...editingPost,
                  hashtags: e.target.value.split(',').map(t => t.trim()).filter(t => t)
                })}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Call to Action"
                value={editingPost.call_to_action}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditingPost({ ...editingPost, call_to_action: e.target.value })}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Visual Prompt"
                value={editingPost.visual_prompt || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditingPost({ ...editingPost, visual_prompt: e.target.value })}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ThreadsPostManager;