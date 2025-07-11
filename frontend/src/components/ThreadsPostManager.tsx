import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Card,
  CardContent,
  CardActions,
  Grid,
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
import axios from 'axios';

interface ThreadsPost {
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

  const handleDeletePost = (index: number) => {
    setPosts(posts.filter((_, i) => i !== index));
  };

  const proceedToSchedule = () => {
    setActiveStep(3);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Post Manager
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Generate, review, and approve Threads posts
      </Typography>

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
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Number of Posts"
                  value={count}
                  onChange={(e) => setCount(parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 20 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Period (Optional)</InputLabel>
                  <Select
                    value={selectedPeriod}
                    onChange={(e) => setSelectedPeriod(e.target.value as number)}
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
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Theme (Optional)"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  placeholder="e.g., Morning motivation, Weekly reflection"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={includeAffirmations}
                      onChange={(e) => setIncludeAffirmations(e.target.checked)}
                    />
                  }
                  label="Include Affirmations"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={includeActivities}
                      onChange={(e) => setIncludeActivities(e.target.checked)}
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
                <Grid item xs={12} md={6} key={index}>
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
                        onClick={() => handleDeletePost(index)}
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
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Approval Status
            </Typography>
            {approvalResult.telegram_simulation && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Telegram Bot Decision: {approvalResult.telegram_simulation.decision}
              </Alert>
            )}
            {approvalResult.decision_result && (
              <Box>
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
                onChange={(e) => setEditingPost({ ...editingPost, content: e.target.value })}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Hashtags (comma separated)"
                value={editingPost.hashtags.join(', ')}
                onChange={(e) => setEditingPost({
                  ...editingPost,
                  hashtags: e.target.value.split(',').map(t => t.trim()).filter(t => t)
                })}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Call to Action"
                value={editingPost.call_to_action}
                onChange={(e) => setEditingPost({ ...editingPost, call_to_action: e.target.value })}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Visual Prompt"
                value={editingPost.visual_prompt || ''}
                onChange={(e) => setEditingPost({ ...editingPost, visual_prompt: e.target.value })}
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