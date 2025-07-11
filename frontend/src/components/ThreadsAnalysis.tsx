import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  Tag as TagIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface AnalysisResult {
  competitor_insights: {
    posting_patterns: {
      frequency: string;
      best_times: string[];
      consistency: string;
    };
    content_strategy: {
      primary_themes: string[];
      content_mix: Record<string, number>;
      hashtag_strategy: string[];
    };
    engagement_tactics: {
      conversation_starters: boolean;
      story_polls: boolean;
      user_generated_content: boolean;
      response_time: string;
    };
    visual_strategy: {
      style: string;
      colors: string[];
      text_overlay: string;
    };
  };
  recommendations: {
    posting_schedule: {
      frequency: string;
      times: string[];
      days: string[];
    };
    content_pillars: Array<{
      name: string;
      percentage: number;
      description: string;
    }>;
    engagement_strategy: string[];
  };
}

const ThreadsAnalysis: React.FC = () => {
  const [handles, setHandles] = useState<string[]>(['']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  const addHandle = () => {
    setHandles([...handles, '']);
  };

  const removeHandle = (index: number) => {
    setHandles(handles.filter((_, i) => i !== index));
  };

  const updateHandle = (index: number, value: string) => {
    const newHandles = [...handles];
    newHandles[index] = value;
    setHandles(newHandles);
  };

  const analyzeProfiles = async () => {
    setLoading(true);
    setError(null);

    try {
      const validHandles = handles.filter(h => h.trim());
      if (validHandles.length === 0) {
        throw new Error('Please enter at least one Threads handle');
      }

      const response = await axios.post('/api/threads/analyze', {
        handles: validHandles,
      });

      if (response.data.success) {
        setAnalysis(response.data.analysis);
      } else {
        throw new Error(response.data.error || 'Analysis failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze profiles');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Analyze Threads Profiles
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Enter Threads handles to analyze their content strategy and get insights
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Threads Handles
          </Typography>
          {handles.map((handle, index) => (
            <Box key={index} sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                fullWidth
                label={`Handle ${index + 1}`}
                value={handle}
                onChange={(e) => updateHandle(index, e.target.value)}
                placeholder="@username"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">@</InputAdornment>
                  ),
                }}
              />
              {handles.length > 1 && (
                <IconButton
                  color="error"
                  onClick={() => removeHandle(index)}
                  aria-label="remove handle"
                >
                  <DeleteIcon />
                </IconButton>
              )}
            </Box>
          ))}
          <Button
            startIcon={<AddIcon />}
            onClick={addHandle}
            variant="outlined"
            sx={{ mr: 2 }}
          >
            Add Handle
          </Button>
          <Button
            startIcon={<AnalyticsIcon />}
            onClick={analyzeProfiles}
            variant="contained"
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Analyze Profiles'}
          </Button>
        </CardContent>
      </Card>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {analysis && (
        <>
          <Grid container spacing={3}>
            {/* Posting Patterns */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <ScheduleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Posting Patterns
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText
                        primary="Frequency"
                        secondary={analysis.competitor_insights.posting_patterns.frequency}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Best Times"
                        secondary={analysis.competitor_insights.posting_patterns.best_times.join(', ')}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Consistency"
                        secondary={analysis.competitor_insights.posting_patterns.consistency}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {/* Content Strategy */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Content Strategy
                  </Typography>
                  <Typography variant="subtitle2" gutterBottom>
                    Primary Themes
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    {analysis.competitor_insights.content_strategy.primary_themes.map((theme, i) => (
                      <Chip key={i} label={theme} size="small" sx={{ m: 0.5 }} />
                    ))}
                  </Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Content Mix
                  </Typography>
                  {Object.entries(analysis.competitor_insights.content_strategy.content_mix).map(([type, percentage]) => (
                    <Box key={type} sx={{ mb: 1 }}>
                      <Typography variant="body2">
                        {type}: {percentage}%
                      </Typography>
                      <Box sx={{ width: `${percentage}%`, bgcolor: 'primary.main', height: 4, borderRadius: 1 }} />
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>

            {/* Engagement Tactics */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Engagement Tactics
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText
                        primary="Conversation Starters"
                        secondary={analysis.competitor_insights.engagement_tactics.conversation_starters ? 'Yes' : 'No'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Story Polls"
                        secondary={analysis.competitor_insights.engagement_tactics.story_polls ? 'Yes' : 'No'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="User Generated Content"
                        secondary={analysis.competitor_insights.engagement_tactics.user_generated_content ? 'Yes' : 'No'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Response Time"
                        secondary={analysis.competitor_insights.engagement_tactics.response_time}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {/* Hashtag Strategy */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <TagIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Hashtag Strategy
                  </Typography>
                  <List dense>
                    {analysis.competitor_insights.content_strategy.hashtag_strategy.map((strategy, i) => (
                      <ListItem key={i}>
                        <ListItemText primary={strategy} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Divider sx={{ my: 4 }} />

          {/* Recommendations */}
          <Typography variant="h5" gutterBottom>
            Recommendations for 7 Cycles
          </Typography>

          <Grid container spacing={3}>
            {/* Posting Schedule */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Recommended Posting Schedule
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText
                        primary="Frequency"
                        secondary={analysis.recommendations.posting_schedule.frequency}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Best Times"
                        secondary={analysis.recommendations.posting_schedule.times.join(', ')}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Best Days"
                        secondary={analysis.recommendations.posting_schedule.days.join(', ')}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {/* Content Pillars */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Content Pillars
                  </Typography>
                  {analysis.recommendations.content_pillars.map((pillar, i) => (
                    <Box key={i} sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">
                        {pillar.name} ({pillar.percentage}%)
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {pillar.description}
                      </Typography>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>

            {/* Engagement Strategy */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Engagement Strategy
                  </Typography>
                  <List dense>
                    {analysis.recommendations.engagement_strategy.map((strategy, i) => (
                      <ListItem key={i}>
                        <ListItemText primary={strategy} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );
};

export default ThreadsAnalysis;