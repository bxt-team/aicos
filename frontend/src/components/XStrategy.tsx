import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Psychology as StrategyIcon,
  ViewColumn as ViewColumnIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  Twitter as TwitterIcon
} from '@mui/icons-material';
import axios from 'axios';

interface ContentPillar {
  name: string;
  description: string;
  cycles: number[];
  content_ratio: string;
  formats: string[];
}

interface StrategyData {
  strategy_date: string;
  content_pillars: Record<string, ContentPillar>;
  tweet_templates: {
    single_tweet: {
      hook_formulas: string[];
      structure: string;
      character_optimization: string;
    };
    thread_structure: {
      opener: string;
      body: string;
      closer: string;
      formatting: string;
    };
    poll_ideas: string[];
  };
  posting_schedule: {
    frequency: string;
    times: string[];
    thread_days: string[];
    poll_days: string[];
    spaces_schedule: string;
  };
  engagement_tactics: {
    reply_strategy: string;
    retweet_strategy: string;
    hashtag_strategy: {
      primary: string[];
      secondary: string[];
      trending: string;
    };
    community_building: string[];
  };
  growth_tactics: {
    follower_acquisition: string[];
    viral_formulas: string[];
    algorithm_optimization: string[];
  };
  content_calendar: Record<string, string>;
  performance_metrics: {
    engagement_rate: string;
    follower_growth: string;
    thread_completion: string;
    profile_visits: string;
    key_metrics: string[];
  };
}

const XStrategy: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [strategy, setStrategy] = useState<StrategyData | null>(null);
  const [hasAnalysis, setHasAnalysis] = useState(false);

  useEffect(() => {
    checkAnalysis();
    loadLatestStrategy();
  }, []);

  const checkAnalysis = async () => {
    try {
      const response = await axios.get('/api/x/analysis/latest');
      setHasAnalysis(response.data.success && !response.data.analysis.error);
    } catch {
      setHasAnalysis(false);
    }
  };

  const loadLatestStrategy = async () => {
    try {
      const response = await axios.get('/api/x/strategy/latest');
      if (response.data.success && !response.data.strategy.error) {
        setStrategy(response.data.strategy);
      }
    } catch (err) {
      // No existing strategy is fine
    }
  };

  const handleCreateStrategy = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/x/strategy', {
        use_latest_analysis: true
      });

      if (response.data.success) {
        setStrategy(response.data.strategy);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create strategy');
    } finally {
      setLoading(false);
    }
  };

  const cycleColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF'];

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <StrategyIcon /> X Content Strategy
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Create a comprehensive content strategy based on analysis insights
        </Typography>

        {!hasAnalysis && (
          <Alert severity="info" sx={{ mb: 2 }}>
            No analysis found. Please run an analysis first to create an optimized strategy.
          </Alert>
        )}

        <Button
          variant="contained"
          onClick={handleCreateStrategy}
          disabled={loading || !hasAnalysis}
          startIcon={loading ? <CircularProgress size={20} /> : <StrategyIcon />}
          fullWidth
        >
          {loading ? 'Creating Strategy...' : 'Create New Strategy'}
        </Button>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      {strategy && (
        <Grid container spacing={3}>
          {/* Content Pillars */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ViewColumnIcon /> Content Pillars
                </Typography>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  {Object.entries(strategy.content_pillars).map(([key, pillar]) => (
                    <Grid size={{ xs: 12, md: 6, lg: 4 }} key={key}>
                      <Paper elevation={2} sx={{ p: 2, height: '100%' }}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          {pillar.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {pillar.description}
                        </Typography>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="caption" color="text.secondary">Cycles:</Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                            {pillar.cycles.map((cycle) => (
                              <Chip
                                key={cycle}
                                label={`Cycle ${cycle}`}
                                size="small"
                                sx={{ 
                                  backgroundColor: cycleColors[cycle - 1],
                                  color: 'white'
                                }}
                              />
                            ))}
                          </Box>
                        </Box>
                        <Typography variant="caption" display="block" sx={{ mb: 1 }}>
                          Content Ratio: <strong>{pillar.content_ratio}</strong>
                        </Typography>
                        <Typography variant="caption" color="text.secondary">Formats:</Typography>
                        <Box sx={{ pl: 2 }}>
                          {pillar.formats.map((format, idx) => (
                            <Typography key={idx} variant="caption" display="block">
                              • {format}
                            </Typography>
                          ))}
                        </Box>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Tweet Templates */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TwitterIcon /> Tweet Templates
                </Typography>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Single Tweet Templates</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="subtitle2" gutterBottom>Hook Formulas:</Typography>
                    <List dense>
                      {strategy.tweet_templates.single_tweet.hook_formulas.map((formula, idx) => (
                        <ListItem key={idx}>
                          <ListItemText 
                            primary={formula}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                    <Typography variant="caption" color="text.secondary">
                      Structure: {strategy.tweet_templates.single_tweet.structure}
                    </Typography>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Thread Structure</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      <ListItem>
                        <ListItemText 
                          primary="Opener"
                          secondary={strategy.tweet_templates.thread_structure.opener}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Body"
                          secondary={strategy.tweet_templates.thread_structure.body}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Closer"
                          secondary={strategy.tweet_templates.thread_structure.closer}
                        />
                      </ListItem>
                    </List>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Poll Ideas</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {strategy.tweet_templates.poll_ideas.map((idea, idx) => (
                        <ListItem key={idx}>
                          <ListItemText primary={idea} />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          </Grid>

          {/* Posting Schedule */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ScheduleIcon /> Posting Schedule
                </Typography>
                
                <List>
                  <ListItem>
                    <ListItemText 
                      primary="Frequency"
                      secondary={strategy.posting_schedule.frequency}
                    />
                  </ListItem>
                  <Divider />
                  <ListItem>
                    <ListItemText 
                      primary="Best Times"
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          {strategy.posting_schedule.times.map((time) => (
                            <Chip
                              key={time}
                              label={time}
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
                      primary="Thread Days"
                      secondary={strategy.posting_schedule.thread_days.join(', ')}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Poll Days"
                      secondary={strategy.posting_schedule.poll_days.join(', ')}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Twitter Spaces"
                      secondary={strategy.posting_schedule.spaces_schedule}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Growth Tactics */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendingUpIcon /> Growth & Performance
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Typography variant="subtitle1" gutterBottom>Viral Formulas</Typography>
                    <List dense>
                      {strategy.growth_tactics.viral_formulas.map((formula, idx) => (
                        <ListItem key={idx}>
                          <ListItemText primary={formula} />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                  
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Typography variant="subtitle1" gutterBottom>Performance Targets</Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell>Engagement Rate</TableCell>
                            <TableCell align="right">{strategy.performance_metrics.engagement_rate}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Follower Growth</TableCell>
                            <TableCell align="right">{strategy.performance_metrics.follower_growth}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Thread Completion</TableCell>
                            <TableCell align="right">{strategy.performance_metrics.thread_completion}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Profile Visits</TableCell>
                            <TableCell align="right">{strategy.performance_metrics.profile_visits}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Content Calendar */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Weekly Content Calendar</Typography>
                <Grid container spacing={1} sx={{ mt: 1 }}>
                  {Object.entries(strategy.content_calendar).map(([day, content]) => (
                    <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={day}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="subtitle2" fontWeight="bold" sx={{ textTransform: 'capitalize' }}>
                          {day}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {content}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default XStrategy;