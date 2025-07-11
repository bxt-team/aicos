import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  CalendarMonth as CalendarIcon,
  AccessTime as TimeIcon,
  TrendingUp as TrendingIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Publish as PublishIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format, parseISO } from 'date-fns';
import axios from 'axios';

interface ScheduledPost {
  post: {
    content: string;
    hashtags: string[];
    period: number;
    post_type: string;
  };
  scheduled_for: string;
  time_category: string;
  day_of_week: string;
  is_peak_time: boolean;
  expected_reach: string;
}

interface Schedule {
  scheduled_posts: ScheduledPost[];
  summary: {
    total_posts: number;
    date_range: string;
    posts_per_week: number;
    distribution: {
      by_day: Record<string, number>;
      by_time: Record<string, number>;
      by_type: Record<string, number>;
    };
    peak_time_percentage: number;
    estimated_high_reach_posts: number;
  };
}

const ThreadsSchedule: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [upcomingPosts, setUpcomingPosts] = useState<ScheduledPost[]>([]);
  
  // Scheduling parameters
  const [startDate, setStartDate] = useState<Date | null>(new Date());
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [postsPerWeek, setPostsPerWeek] = useState(3);
  
  // Edit dialog
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingPost, setEditingPost] = useState<ScheduledPost | null>(null);

  useEffect(() => {
    loadLatestSchedule();
    loadUpcomingPosts();
  }, []);

  const loadLatestSchedule = async () => {
    try {
      const response = await axios.get('/api/threads/schedule/latest');
      setSchedule(response.data);
    } catch (err) {
      // No schedule yet
    }
  };

  const loadUpcomingPosts = async () => {
    try {
      const response = await axios.get('/api/threads/schedule/upcoming?days=7');
      setUpcomingPosts(response.data.upcoming_posts);
    } catch (err) {
      // No upcoming posts
    }
  };

  const createSchedule = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post('/api/threads/schedule', {
        start_date: startDate?.toISOString(),
        end_date: endDate?.toISOString(),
        posts_per_week: postsPerWeek,
      });

      if (response.data.success) {
        setSchedule(response.data);
        setSuccess('Schedule created successfully!');
        loadUpcomingPosts();
      } else {
        throw new Error(response.data.error || 'Scheduling failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create schedule');
    } finally {
      setLoading(false);
    }
  };

  const publishNow = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/threads/publish');
      setSuccess(response.data.message);
    } catch (err: any) {
      setError(err.message || 'Failed to publish posts');
    } finally {
      setLoading(false);
    }
  };

  const getReachColor = (reach: string) => {
    switch (reach) {
      case 'very_high':
        return 'success';
      case 'high':
        return 'primary';
      case 'medium':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getTimeIcon = (timeCategory: string) => {
    switch (timeCategory) {
      case 'morning':
        return '🌅';
      case 'midday':
        return '☀️';
      case 'evening':
        return '🌆';
      default:
        return '🕐';
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Content Schedule
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Schedule your approved posts for optimal engagement
      </Typography>

      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Schedule Configuration
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <DatePicker
                  label="Start Date"
                  value={startDate}
                  onChange={setStartDate}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <DatePicker
                  label="End Date (Optional)"
                  value={endDate}
                  onChange={setEndDate}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="Posts per Week"
                  value={postsPerWeek}
                  onChange={(e) => setPostsPerWeek(parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 7 }}
                />
              </Grid>
            </Grid>
            <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
              <Button
                startIcon={<ScheduleIcon />}
                onClick={createSchedule}
                variant="contained"
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Schedule'}
              </Button>
              <Button
                startIcon={<PublishIcon />}
                onClick={publishNow}
                variant="outlined"
                disabled={loading}
              >
                Publish Ready Posts
              </Button>
            </Box>
          </CardContent>
        </Card>
      </LocalizationProvider>

      {/* Upcoming Posts */}
      {upcomingPosts.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upcoming Posts (Next 7 Days)
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Date & Time</TableCell>
                    <TableCell>Content Preview</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Expected Reach</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {upcomingPosts.map((post, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Box>
                          <Typography variant="body2">
                            {format(parseISO(post.scheduled_for), 'MMM dd, yyyy')}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {getTimeIcon(post.time_category)} {format(parseISO(post.scheduled_for), 'HH:mm')}
                            {post.is_peak_time && ' ⭐'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={post.post.content}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                            {post.post.content}
                          </Typography>
                        </Tooltip>
                        <Box sx={{ mt: 0.5 }}>
                          {post.post.hashtags.slice(0, 3).map((tag, i) => (
                            <Chip key={i} label={tag} size="small" sx={{ mr: 0.5 }} />
                          ))}
                          {post.post.hashtags.length > 3 && (
                            <Chip label={`+${post.post.hashtags.length - 3}`} size="small" />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={post.post.post_type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={post.expected_reach.replace('_', ' ')}
                          size="small"
                          color={getReachColor(post.expected_reach)}
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton size="small" onClick={() => {
                          setEditingPost(post);
                          setEditDialogOpen(true);
                        }}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Schedule Summary */}
      {schedule && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Schedule Overview
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Date Range
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {schedule.summary.date_range}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Posts
                </Typography>
                <Typography variant="h4" color="primary">
                  {schedule.summary.total_posts}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Posts per Week
                </Typography>
                <Typography variant="body1">
                  {schedule.summary.posts_per_week}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Metrics
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Peak Time Coverage
                  </Typography>
                  <Typography variant="h5" color="primary">
                    {schedule.summary.peak_time_percentage.toFixed(0)}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    High Reach Posts
                  </Typography>
                  <Typography variant="h5" color="success.main">
                    {schedule.summary.estimated_high_reach_posts}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Distribution by Day
                </Typography>
                {Object.entries(schedule.summary.distribution.by_day).map(([day, count]) => (
                  <Box key={day} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">{day}</Typography>
                      <Typography variant="body2">{count}</Typography>
                    </Box>
                    <Box sx={{ 
                      width: `${(count / schedule.summary.total_posts) * 100}%`,
                      height: 4,
                      bgcolor: 'primary.main',
                      borderRadius: 1
                    }} />
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
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
        <DialogTitle>Edit Scheduled Post</DialogTitle>
        <DialogContent>
          {editingPost && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Current Schedule: {format(parseISO(editingPost.scheduled_for), 'PPpp')}
              </Typography>
              <Typography variant="body1" paragraph>
                {editingPost.post.content}
              </Typography>
              <Alert severity="info">
                Editing scheduled posts will be available in a future update.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ThreadsSchedule;