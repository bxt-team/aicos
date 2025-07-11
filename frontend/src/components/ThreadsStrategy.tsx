import React, { useState, useEffect } from 'react';
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Strategy as StrategyIcon,
  CalendarMonth as CalendarIcon,
  Tag as TagIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface ContentPillar {
  name: string;
  percentage: number;
  description: string;
  topics: string[];
  post_types: string[];
}

interface Strategy {
  content_pillars: ContentPillar[];
  posting_schedule: {
    frequency: string;
    optimal_times: Record<string, string>;
    best_days: string[];
    avoid_days: string[];
  };
  hashtag_strategy: {
    brand_hashtags: string[];
    discovery_hashtags: string[];
    period_hashtags: Record<string, string[]>;
    usage_guidelines: string;
  };
  engagement_tactics: Array<{
    tactic: string;
    frequency: string;
    description: string;
  }>;
  kpis: {
    growth_targets: Record<string, string>;
    content_metrics: Record<string, string>;
    milestones: Array<{
      month: number;
      followers: number;
      posts: number;
    }>;
  };
}

const ThreadsStrategy: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [targetAudience, setTargetAudience] = useState('');
  const [hasAnalysis, setHasAnalysis] = useState(false);

  useEffect(() => {
    checkForAnalysis();
  }, []);

  const checkForAnalysis = async () => {
    try {
      const response = await axios.get('/api/threads/analysis/latest');
      setHasAnalysis(!!response.data);
    } catch (err) {
      setHasAnalysis(false);
    }
  };

  const createStrategy = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/threads/strategy', {
        target_audience: targetAudience || undefined,
      });

      if (response.data.success) {
        setStrategy(response.data.strategy);
      } else {
        throw new Error(response.data.error || 'Strategy creation failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create strategy');
    } finally {
      setLoading(false);
    }
  };

  const loadLatestStrategy = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get('/api/threads/strategy/latest');
      setStrategy(response.data);
    } catch (err: any) {
      setError('No strategy found. Create one first.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Content Strategy
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Create a comprehensive content strategy based on competitive analysis
      </Typography>

      {!hasAnalysis && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          No analysis found. Please analyze Threads profiles first to create an informed strategy.
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Strategy Configuration
          </Typography>
          <TextField
            fullWidth
            label="Target Audience (Optional)"
            value={targetAudience}
            onChange={(e) => setTargetAudience(e.target.value)}
            placeholder="e.g., Spiritually curious individuals seeking personal growth"
            sx={{ mb: 2 }}
            multiline
            rows={2}
          />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              startIcon={<StrategyIcon />}
              onClick={createStrategy}
              variant="contained"
              disabled={loading || !hasAnalysis}
            >
              {loading ? 'Creating...' : 'Create Strategy'}
            </Button>
            <Button
              onClick={loadLatestStrategy}
              variant="outlined"
              disabled={loading}
            >
              Load Latest Strategy
            </Button>
          </Box>
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

      {strategy && (
        <>
          {/* Content Pillars */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Content Pillars</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {strategy.content_pillars.map((pillar, index) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Typography variant="h6" sx={{ flex: 1 }}>
                            {pillar.name}
                          </Typography>
                          <Chip
                            label={`${pillar.percentage}%`}
                            color="primary"
                            size="small"
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {pillar.description}
                        </Typography>
                        <Typography variant="subtitle2" gutterBottom>
                          Topics:
                        </Typography>
                        <Box sx={{ mb: 1 }}>
                          {pillar.topics.map((topic, i) => (
                            <Chip
                              key={i}
                              label={topic}
                              size="small"
                              variant="outlined"
                              sx={{ m: 0.5 }}
                            />
                          ))}
                        </Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Post Types:
                        </Typography>
                        <Box>
                          {pillar.post_types.map((type, i) => (
                            <Chip
                              key={i}
                              label={type}
                              size="small"
                              color="secondary"
                              variant="outlined"
                              sx={{ m: 0.5 }}
                            />
                          ))}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Content Distribution
                </Typography>
                <Box sx={{ display: 'flex', height: 20, borderRadius: 1, overflow: 'hidden' }}>
                  {strategy.content_pillars.map((pillar, index) => (
                    <Box
                      key={index}
                      sx={{
                        width: `${pillar.percentage}%`,
                        bgcolor: `primary.${index % 2 === 0 ? 'main' : 'light'}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {pillar.percentage > 10 && (
                        <Typography variant="caption" sx={{ color: 'white' }}>
                          {pillar.percentage}%
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Box>
              </Box>
            </AccordionDetails>
          </Accordion>

          {/* Posting Schedule */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">
                <CalendarIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Posting Schedule
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Frequency
                  </Typography>
                  <Typography variant="h5" color="primary" gutterBottom>
                    {strategy.posting_schedule.frequency}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Best Days
                  </Typography>
                  <Box>
                    {strategy.posting_schedule.best_days.map((day, i) => (
                      <Chip key={i} label={day} color="success" sx={{ m: 0.5 }} />
                    ))}
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>
                    Optimal Times
                  </Typography>
                  <Grid container spacing={2}>
                    {Object.entries(strategy.posting_schedule.optimal_times).map(([period, time]) => (
                      <Grid item xs={12} sm={4} key={period}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="subtitle2" color="text.secondary">
                              {period.charAt(0).toUpperCase() + period.slice(1)}
                            </Typography>
                            <Typography variant="h6">{time}</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* Hashtag Strategy */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">
                <TagIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Hashtag Strategy
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" color="text.secondary" paragraph>
                {strategy.hashtag_strategy.usage_guidelines}
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Brand Hashtags
                  </Typography>
                  <Box>
                    {strategy.hashtag_strategy.brand_hashtags.map((tag, i) => (
                      <Chip key={i} label={tag} color="primary" sx={{ m: 0.5 }} />
                    ))}
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Discovery Hashtags
                  </Typography>
                  <Box>
                    {strategy.hashtag_strategy.discovery_hashtags.map((tag, i) => (
                      <Chip key={i} label={tag} variant="outlined" sx={{ m: 0.5 }} />
                    ))}
                  </Box>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* Engagement Tactics */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Engagement Tactics</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Tactic</TableCell>
                      <TableCell>Frequency</TableCell>
                      <TableCell>Description</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {strategy.engagement_tactics.map((tactic, i) => (
                      <TableRow key={i}>
                        <TableCell>{tactic.tactic}</TableCell>
                        <TableCell>{tactic.frequency}</TableCell>
                        <TableCell>{tactic.description}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>

          {/* KPIs */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">
                <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                KPIs & Growth Targets
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Growth Targets
                  </Typography>
                  <List dense>
                    {Object.entries(strategy.kpis.growth_targets).map(([metric, target]) => (
                      <ListItem key={metric}>
                        <ListItemText
                          primary={metric.charAt(0).toUpperCase() + metric.slice(1)}
                          secondary={target}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Milestones
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Month</TableCell>
                          <TableCell align="right">Followers</TableCell>
                          <TableCell align="right">Posts</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {strategy.kpis.milestones.map((milestone, i) => (
                          <TableRow key={i}>
                            <TableCell>{milestone.month}</TableCell>
                            <TableCell align="right">{milestone.followers}</TableCell>
                            <TableCell align="right">{milestone.posts}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </>
      )}
    </Box>
  );
};

export default ThreadsStrategy;