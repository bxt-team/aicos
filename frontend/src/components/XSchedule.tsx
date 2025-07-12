import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Badge,
  Tabs,
  Tab
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  Twitter as TwitterIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayArrowIcon,
  AccessTime as AccessTimeIcon,
  CalendarToday as CalendarTodayIcon,
  TrendingUp as TrendingUpIcon,
  Link as LinkIcon,
  Poll as PollIcon
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import axios from 'axios';
import { format, addDays, isSameDay, parseISO } from 'date-fns';

interface ScheduledPost {
  id: string;
  post: {
    content: string;
    type: string;
    hashtags: string[];
    period: number;
    thread_content?: string[];
    poll_options?: string[];
  };
  scheduled_for: string;
  timezone: string;
  status: string;
  rationale: string;
  expected_reach: {
    impressions: number;
    engagements: number;
    profile_clicks: number;
    confidence: string;
  };
}

interface ScheduleSummary {
  first_post: string;
  last_post: string;
  daily_distribution: Record<string, number>;
  type_distribution: Record<string, number>;
}

const XSchedule: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scheduledPosts, setScheduledPosts] = useState<ScheduledPost[]>([]);
  const [scheduleSummary, setScheduleSummary] = useState<ScheduleSummary | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());
  const [rescheduleDialog, setRescheduleDialog] = useState<{ open: boolean; post: ScheduledPost | null }>({
    open: false,
    post: null
  });
  const [newScheduleTime, setNewScheduleTime] = useState<Date | null>(null);
  const [publishingStatus, setPublishingStatus] = useState<Record<string, string>>({});

  useEffect(() => {
    loadSchedule();
  }, []);

  const loadSchedule = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/x/schedule/upcoming?days=30');
      if (response.data.success) {
        setScheduledPosts(response.data.upcoming_posts);
      }

      const summaryResponse = await axios.get('/api/x/schedule/latest');
      if (summaryResponse.data.success && !summaryResponse.data.schedule.error) {
        setScheduleSummary(summaryResponse.data.schedule.schedule_summary);
      }
    } catch (err) {
      setError('Failed to load schedule');
    } finally {
      setLoading(false);
    }
  };

  const handlePublishNow = async (postId: string) => {
    setPublishingStatus({ ...publishingStatus, [postId]: 'publishing' });
    
    try {
      const response = await axios.post('/api/x/publish');
      if (response.data.success) {
        setPublishingStatus({ ...publishingStatus, [postId]: 'published' });
        loadSchedule(); // Reload to update status
      }
    } catch (err) {
      setPublishingStatus({ ...publishingStatus, [postId]: 'error' });
      setError('Failed to publish posts');
    }
  };

  const handleReschedule = async () => {
    if (!rescheduleDialog.post || !newScheduleTime) return;

    setLoading(true);
    try {
      const response = await axios.post('/api/x/schedule/reschedule', {
        post_id: rescheduleDialog.post.id,
        new_time: newScheduleTime.toISOString()
      });

      if (response.data.success) {
        loadSchedule();
        setRescheduleDialog({ open: false, post: null });
        setNewScheduleTime(null);
      }
    } catch (err) {
      setError('Failed to reschedule post');
    } finally {
      setLoading(false);
    }
  };

  const getPostIcon = (type: string) => {
    switch (type) {
      case 'thread':
        return <LinkIcon />;
      case 'poll':
        return <PollIcon />;
      default:
        return <TwitterIcon />;
    }
  };

  const getPostsForDate = (date: Date) => {
    return scheduledPosts.filter(post => 
      isSameDay(parseISO(post.scheduled_for), date)
    );
  };

  const formatTime = (isoString: string) => {
    return format(parseISO(isoString), 'h:mm a');
  };

  const formatDate = (isoString: string) => {
    return format(parseISO(isoString), 'MMM d, yyyy');
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ScheduleIcon /> X Content Schedule
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Manage your X posting schedule and track performance
        </Typography>

        {scheduleSummary && (
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Total Scheduled
                  </Typography>
                  <Typography variant="h4">
                    {scheduledPosts.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Next Post
                  </Typography>
                  <Typography variant="body1">
                    {scheduleSummary.first_post ? formatTime(scheduleSummary.first_post) : 'None'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Daily Average
                  </Typography>
                  <Typography variant="h4">
                    {Object.values(scheduleSummary.daily_distribution).reduce((a, b) => a + b, 0) / 
                     Object.keys(scheduleSummary.daily_distribution).length || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Content Mix
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                    {Object.entries(scheduleSummary.type_distribution).map(([type, count]) => (
                      <Chip
                        key={type}
                        label={`${type}: ${count}`}
                        size="small"
                        icon={getPostIcon(type)}
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Paper>

      <Paper>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          <Tab label="List View" />
          <Tab label="Calendar View" />
          <Tab label="Analytics" />
        </Tabs>

        {activeTab === 0 && (
          <Box sx={{ p: 3 }}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <List>
                {scheduledPosts.map((post) => (
                  <ListItem
                    key={post.id}
                    sx={{
                      mb: 2,
                      bgcolor: 'background.paper',
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider'
                    }}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        {getPostIcon(post.post.type)}
                        <Chip label={`Cycle ${post.post.period}`} size="small" />
                        <Chip
                          label={post.status}
                          size="small"
                          color={post.status === 'published' ? 'success' : 'default'}
                        />
                        <Typography variant="body2" color="text.secondary">
                          <AccessTimeIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                          {formatDate(post.scheduled_for)} at {formatTime(post.scheduled_for)}
                        </Typography>
                      </Box>
                      
                      <Typography variant="body1" sx={{ mb: 1 }}>
                        {post.post.content.substring(0, 140)}...
                      </Typography>
                      
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
                        {post.post.hashtags.map((tag) => (
                          <Chip key={tag} label={tag} size="small" variant="outlined" />
                        ))}
                      </Box>
                      
                      <Typography variant="caption" color="text.secondary">
                        {post.rationale}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                        <Tooltip title="Expected impressions">
                          <Typography variant="caption">
                            <TrendingUpIcon sx={{ fontSize: 14, mr: 0.5 }} />
                            {post.expected_reach.impressions.toLocaleString()}
                          </Typography>
                        </Tooltip>
                        <Typography variant="caption" color="text.secondary">
                          Confidence: {post.expected_reach.confidence}
                        </Typography>
                      </Box>
                    </Box>
                    
                    <ListItemSecondaryAction>
                      <IconButton
                        onClick={() => {
                          setRescheduleDialog({ open: true, post });
                          setNewScheduleTime(parseISO(post.scheduled_for));
                        }}
                        disabled={post.status === 'published'}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        onClick={() => handlePublishNow(post.id)}
                        disabled={post.status === 'published' || publishingStatus[post.id] === 'publishing'}
                      >
                        {publishingStatus[post.id] === 'publishing' ? (
                          <CircularProgress size={20} />
                        ) : (
                          <PlayArrowIcon />
                        )}
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        )}

        {activeTab === 1 && (
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 4 }}>
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                  <DateTimePicker
                    label="Select Date"
                    value={selectedDate}
                    onChange={setSelectedDate}
                  />
                </LocalizationProvider>
              </Grid>
              <Grid size={12}>
                {selectedDate && (
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Posts for {format(selectedDate, 'MMMM d, yyyy')}
                      </Typography>
                      <List>
                        {getPostsForDate(selectedDate).map((post) => (
                          <ListItem key={post.id}>
                            <ListItemText
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  {getPostIcon(post.post.type)}
                                  <Typography variant="body2">
                                    {formatTime(post.scheduled_for)}
                                  </Typography>
                                </Box>
                              }
                              secondary={post.post.content.substring(0, 100) + '...'}
                            />
                          </ListItem>
                        ))}
                        {getPostsForDate(selectedDate).length === 0 && (
                          <Typography variant="body2" color="text.secondary">
                            No posts scheduled for this date
                          </Typography>
                        )}
                      </List>
                    </CardContent>
                  </Card>
                )}
              </Grid>
            </Grid>
          </Box>
        )}

        {activeTab === 2 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Performance Analytics
            </Typography>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Estimated Total Reach
                    </Typography>
                    <Typography variant="h3">
                      {scheduledPosts.reduce((sum, post) => sum + post.expected_reach.impressions, 0).toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Across {scheduledPosts.length} scheduled posts
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Post Type Performance
                    </Typography>
                    <List dense>
                      {scheduleSummary && Object.entries(scheduleSummary.type_distribution).map(([type, count]) => {
                        const avgReach = scheduledPosts
                          .filter(p => p.post.type === type)
                          .reduce((sum, p) => sum + p.expected_reach.impressions, 0) / count;
                        
                        return (
                          <ListItem key={type}>
                            <ListItemText
                              primary={type}
                              secondary={`${count} posts, avg reach: ${Math.round(avgReach).toLocaleString()}`}
                            />
                          </ListItem>
                        );
                      })}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>

      {/* Reschedule Dialog */}
      <Dialog
        open={rescheduleDialog.open}
        onClose={() => setRescheduleDialog({ open: false, post: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reschedule Post</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DateTimePicker
              label="New Schedule Time"
              value={newScheduleTime}
              onChange={setNewScheduleTime}
              sx={{ mt: 2, width: '100%' }}
            />
          </LocalizationProvider>
          
          {rescheduleDialog.post && (
            <Box sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Post Preview:
              </Typography>
              <Typography variant="body2">
                {rescheduleDialog.post.post.content.substring(0, 200)}...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRescheduleDialog({ open: false, post: null })}>
            Cancel
          </Button>
          <Button
            onClick={handleReschedule}
            variant="contained"
            disabled={!newScheduleTime || loading}
          >
            {loading ? <CircularProgress size={20} /> : 'Reschedule'}
          </Button>
        </DialogActions>
      </Dialog>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default XSchedule;