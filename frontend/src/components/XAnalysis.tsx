import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  Chip,
  Grid,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Twitter as TwitterIcon,
  Add as AddIcon,
  Clear as ClearIcon,
  Analytics as AnalyticsIcon,
  Timeline as TimelineIcon,
  Tag as TagIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import axios from 'axios';

interface AnalysisResult {
  profiles_analyzed: string[];
  analysis_date: string;
  content_patterns: {
    tweet_types: Record<string, string>;
    average_length: string;
    thread_strategy: string;
    media_usage: string;
  };
  engagement_tactics: {
    hashtags: string[];
    optimal_hashtag_count: string;
    mention_strategy: string;
    cta_examples: string[];
  };
  posting_strategy: {
    frequency: string;
    peak_times: string[];
    thread_days: string[];
    engagement_windows: string;
  };
  audience_insights: {
    average_engagement: Record<string, string>;
    viral_indicators: string;
    community_type: string;
  };
  content_themes: {
    primary: string[];
    secondary: string[];
    content_mix: string;
  };
  recommendations: {
    quick_wins: string[];
    long_term: string[];
  };
}

const XAnalysis: React.FC = () => {
  const [handles, setHandles] = useState<string[]>(['']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  const addHandle = () => {
    setHandles([...handles, '']);
  };

  const removeHandle = (index: number) => {
    const newHandles = handles.filter((_, i) => i !== index);
    setHandles(newHandles.length ? newHandles : ['']);
  };

  const updateHandle = (index: number, value: string) => {
    const newHandles = [...handles];
    newHandles[index] = value;
    setHandles(newHandles);
  };

  const handleAnalyze = async () => {
    const validHandles = handles.filter(h => h.trim());
    if (!validHandles.length) {
      setError('Please enter at least one X handle');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/x/analyze', {
        profile_handles: validHandles
      });

      if (response.data.success) {
        setAnalysis(response.data.analysis);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze profiles');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TwitterIcon /> X Profile Analysis
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Enter X handles to analyze their content patterns and engagement strategies
        </Typography>

        <Box sx={{ mb: 3 }}>
          {handles.map((handle, index) => (
            <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1 }}>
              <TextField
                fullWidth
                label={`X Handle ${index + 1}`}
                value={handle}
                onChange={(e) => updateHandle(index, e.target.value)}
                placeholder="@username"
                size="small"
                InputProps={{
                  startAdornment: <TwitterIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
              <IconButton onClick={() => removeHandle(index)} disabled={handles.length === 1}>
                <ClearIcon />
              </IconButton>
            </Box>
          ))}
          
          <Button
            startIcon={<AddIcon />}
            onClick={addHandle}
            size="small"
            sx={{ mt: 1 }}
          >
            Add Another Handle
          </Button>
        </Box>

        <Button
          variant="contained"
          onClick={handleAnalyze}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : <AnalyticsIcon />}
          fullWidth
        >
          {loading ? 'Analyzing...' : 'Analyze Profiles'}
        </Button>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      {analysis && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TimelineIcon /> Content Patterns
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Tweet Types Distribution"
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          {Object.entries(analysis.content_patterns.tweet_types).map(([type, percentage]) => (
                            <Chip
                              key={type}
                              label={`${type}: ${percentage}`}
                              size="small"
                              sx={{ mr: 1, mb: 1 }}
                            />
                          ))}
                        </Box>
                      }
                    />
                  </ListItem>
                  <Divider />
                  <ListItem>
                    <ListItemText 
                      primary="Average Tweet Length"
                      secondary={analysis.content_patterns.average_length}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Thread Strategy"
                      secondary={analysis.content_patterns.thread_strategy}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Media Usage"
                      secondary={analysis.content_patterns.media_usage}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TagIcon /> Engagement Tactics
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Top Hashtags"
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          {analysis.engagement_tactics.hashtags.map((tag) => (
                            <Chip
                              key={tag}
                              label={tag}
                              size="small"
                              color="primary"
                              variant="outlined"
                              sx={{ mr: 1, mb: 1 }}
                            />
                          ))}
                        </Box>
                      }
                    />
                  </ListItem>
                  <Divider />
                  <ListItem>
                    <ListItemText 
                      primary="Optimal Hashtag Count"
                      secondary={analysis.engagement_tactics.optimal_hashtag_count}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Call-to-Action Examples"
                      secondary={
                        <Box component="ul" sx={{ mt: 1, pl: 2 }}>
                          {analysis.engagement_tactics.cta_examples.map((cta, idx) => (
                            <li key={idx}>{cta}</li>
                          ))}
                        </Box>
                      }
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ScheduleIcon /> Posting Strategy
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Posting Frequency"
                      secondary={analysis.posting_strategy.frequency}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Peak Times"
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          {analysis.posting_strategy.peak_times.map((time) => (
                            <Chip
                              key={time}
                              label={time}
                              size="small"
                              color="secondary"
                              sx={{ mr: 1, mb: 1 }}
                            />
                          ))}
                        </Box>
                      }
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Thread Days"
                      secondary={analysis.posting_strategy.thread_days.join(', ')}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recommendations
                </Typography>
                <Typography variant="subtitle2" color="primary" sx={{ mt: 2, mb: 1 }}>
                  Quick Wins:
                </Typography>
                <Box component="ul" sx={{ pl: 2 }}>
                  {analysis.recommendations.quick_wins.map((win, idx) => (
                    <li key={idx}>{win}</li>
                  ))}
                </Box>
                <Typography variant="subtitle2" color="primary" sx={{ mt: 2, mb: 1 }}>
                  Long-term Strategy:
                </Typography>
                <Box component="ul" sx={{ pl: 2 }}>
                  {analysis.recommendations.long_term.map((strategy, idx) => (
                    <li key={idx}>{strategy}</li>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default XAnalysis;