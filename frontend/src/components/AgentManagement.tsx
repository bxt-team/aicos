import React, { useState, useEffect } from 'react';
import { agentConfigs, AgentConfig } from '../config/agents';
import axios from 'axios';
import './AgentManagement.css';
import {
  Box,
  TextField,
  FormControl,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Avatar,
  Chip,
  Typography,
  Button,
  Collapse,
  Divider,
  Card,
  CardContent,
  IconButton,
  InputAdornment,
  SelectChangeEvent,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterListIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Launch as LaunchIcon,
  SmartToy as SmartToyIcon,
} from '@mui/icons-material';

interface AgentPrompt {
  name: string;
  role: string;
  goal: string;
  backstory: string;
  settings: {
    verbose: boolean;
    allow_delegation: boolean;
    max_iter: number;
    max_execution_time: number;
  };
}

const AgentManagement: React.FC = () => {
  const [agents] = useState<AgentConfig[]>(agentConfigs);
  // Removed health status - all agents are assumed to be always up
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
  const [agentPrompts, setAgentPrompts] = useState<{ [key: string]: AgentPrompt }>({});
  const [loadingPrompts, setLoadingPrompts] = useState<Set<string>>(new Set());
  
  // Filtering state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Removed health check - all agents are assumed to be always up

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleString('en-US');
  };

  const getStatusIcon = (agentId: string) => {
    return '✅';
  };

  const getStatusText = (agentId: string) => {
    return 'Online';
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Knowledge & Research': '#667eea',
      'Personal Development': '#48bb78',
      'Social Media Marketing': '#ed8936',
      'Visual Content': '#9f7aea',
      'Content Creation': '#38b2ac',
      'Email Marketing': '#f56565',
      'Video Content': '#ec4899',
      'Education': '#3182ce',
      'Analytics': '#319795',
      'Quality Assurance': '#059669',
      'System Management': '#4b5563'
    };
    return colors[category] || '#718096';
  };

  // Get CSS class for category instead of inline style
  const getCategoryClass = (category: string) => {
    const categoryMap: { [key: string]: string } = {
      'Knowledge & Research': 'category-knowledge',
      'Personal Development': 'category-personality',
      'Social Media Marketing': 'category-social',
      'Visual Content': 'category-visual',
      'Content Creation': 'category-content',
      'Email Marketing': 'category-email',
      'Video Content': 'category-video',
      'Education': 'category-education',
      'Analytics': 'category-analytics',
      'Quality Assurance': 'category-qa',
      'System Management': 'category-system'
    };
    return categoryMap[category] || 'category-default';
  };

  const loadAgentPrompt = async (agentId: string) => {
    // Map frontend agent IDs to backend agent IDs
    const agentIdMap: { [key: string]: string } = {
      'qa': 'qa_agent',
      'affirmations': 'affirmations_agent',
      'instagram-posts': 'instagram_ai_prompt_agent',
      'visual-posts': 'visual_post_creator_agent',
      'instagram-poster': 'instagram_poster_agent',
      'instagram-analyzer': 'instagram_analyzer_agent',
      'workflows': 'content_workflow_agent',
      'post-composition': 'post_composition_agent',
      'video-generation': 'video_generation_agent',
      'instagram-reel': 'instagram_reel_agent',
      'android-test': 'android_testing_agent',
      'voice-over': 'voice_over_agent',
      'mobile-analytics': 'mobile_analytics_agent',
      'threads': 'threads_analysis_agent',
      'x-twitter': 'x_analysis_agent'
    };

    const backendAgentId = agentIdMap[agentId];
    if (!backendAgentId) return;

    setLoadingPrompts(prev => new Set(prev).add(agentId));
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/agent-prompts/${backendAgentId}`);
      if (response.data.success) {
        setAgentPrompts(prev => ({
          ...prev,
          [agentId]: response.data.agent
        }));
      }
    } catch (error) {
      console.error(`Error loading prompt for agent ${agentId}:`, error);
    } finally {
      setLoadingPrompts(prev => {
        const newSet = new Set(prev);
        newSet.delete(agentId);
        return newSet;
      });
    }
  };

  const toggleAgentExpansion = async (agentId: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId);
    } else {
      newExpanded.add(agentId);
      // Load prompts if not already loaded
      if (!agentPrompts[agentId] && !loadingPrompts.has(agentId)) {
        await loadAgentPrompt(agentId);
      }
    }
    setExpandedAgents(newExpanded);
  };

  const formatBackstory = (backstory: string) => {
    return backstory.split('\n').map((line, index) => {
      if (line.trim().startsWith('-')) {
        return <li key={index}>{line.trim().substring(1).trim()}</li>;
      }
      if (line.trim() === '') {
        return <br key={index} />;
      }
      return <p key={index}>{line}</p>;
    });
  };

  // Get unique categories
  const categories = Array.from(new Set(agents.map(a => a.category))).sort();
  
  // Filter agents
  const filteredAgents = agents
    .filter(agent => agent.enabled)
    .filter(agent => 
      selectedCategory === 'all' || agent.category === selectedCategory
    )
    .filter(agent => {
      const searchLower = searchTerm.toLowerCase();
      return agent.name.toLowerCase().includes(searchLower) ||
             agent.description.toLowerCase().includes(searchLower) ||
             agent.features.some(feature => feature.toLowerCase().includes(searchLower));
    });

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <SmartToyIcon /> Active Agents
      </Typography>
      
      {/* Search and Filter Controls */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          placeholder="Search agents by name, description, or features..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ maxWidth: 600 }}
        />
        <FormControl sx={{ minWidth: 200 }}>
          <Select
            value={selectedCategory}
            onChange={(e: SelectChangeEvent) => setSelectedCategory(e.target.value)}
            displayEmpty
            startAdornment={
              <InputAdornment position="start">
                <FilterListIcon />
              </InputAdornment>
            }
          >
            <MenuItem value="all">All Categories</MenuItem>
            {categories.map(cat => (
              <MenuItem key={cat} value={cat}>{cat}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Agents List */}
      <List sx={{ bgcolor: 'background.paper', borderRadius: 2 }}>
        {filteredAgents.length === 0 ? (
          <ListItem>
            <ListItemText 
              primary="No agents found"
              secondary={searchTerm || selectedCategory !== 'all' 
                ? 'Try adjusting your search criteria' 
                : 'No agents are currently enabled'}
              sx={{ textAlign: 'center', py: 4 }}
            />
          </ListItem>
        ) : (
          filteredAgents.map((agent, index) => (
            <React.Fragment key={agent.id}>
              {index > 0 && <Divider />}
              <ListItem disablePadding>
                <ListItemButton onClick={() => toggleAgentExpansion(agent.id)}>
                  <ListItemIcon>
                    <Avatar sx={{ bgcolor: getCategoryColor(agent.category), width: 48, height: 48 }}>
                      <Typography fontSize="large">{agent.icon}</Typography>
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="h6">{agent.name}</Typography>
                        <Chip 
                          label={agent.category} 
                          size="small" 
                          sx={{ 
                            bgcolor: getCategoryColor(agent.category) + '20',
                            color: getCategoryColor(agent.category),
                            fontWeight: 500
                          }}
                        />
                        <Chip 
                          label={getStatusText(agent.id)} 
                          size="small" 
                          color="success"
                          icon={<Typography fontSize="small">{getStatusIcon(agent.id)}</Typography>}
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {agent.description}
                        </Typography>
                        <Box display="flex" gap={0.5} flexWrap="wrap">
                          {agent.features.map((feature, idx) => (
                            <Chip 
                              key={idx} 
                              label={feature} 
                              size="small" 
                              variant="outlined"
                              sx={{ fontSize: '0.75rem' }}
                            />
                          ))}
                        </Box>
                      </Box>
                    }
                  />
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Button
                      variant="contained"
                      startIcon={<LaunchIcon />}
                      href={agent.route}
                      size="small"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Open
                    </Button>
                    <IconButton>
                      {expandedAgents.has(agent.id) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  </Box>
                </ListItemButton>
              </ListItem>
              
              {/* Expanded Agent Details */}
              <Collapse in={expandedAgents.has(agent.id)} timeout="auto" unmountOnExit>
                <Box sx={{ px: 3, py: 2, bgcolor: 'grey.50' }}>
                  {loadingPrompts.has(agent.id) ? (
                    <Typography align="center" color="text.secondary">Loading agent configuration...</Typography>
                  ) : agentPrompts[agent.id] ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                        <Card variant="outlined" sx={{ flex: 1, minWidth: 300 }}>
                          <CardContent>
                            <Typography variant="h6" gutterBottom color="primary">
                              🎯 Role & Goal
                            </Typography>
                            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                              Role:
                            </Typography>
                            <Typography variant="body2" paragraph>
                              {agentPrompts[agent.id].role}
                            </Typography>
                            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                              Goal:
                            </Typography>
                            <Typography variant="body2">
                              {agentPrompts[agent.id].goal}
                            </Typography>
                          </CardContent>
                        </Card>
                        
                        <Card variant="outlined" sx={{ flex: 1, minWidth: 300 }}>
                          <CardContent>
                            <Typography variant="h6" gutterBottom color="primary">
                              ⚙️ Settings
                            </Typography>
                            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  Verbose:
                                </Typography>
                                <Typography variant="body2">
                                  {agentPrompts[agent.id].settings.verbose ? 'Yes' : 'No'}
                                </Typography>
                              </Box>
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  Allow Delegation:
                                </Typography>
                                <Typography variant="body2">
                                  {agentPrompts[agent.id].settings.allow_delegation ? 'Yes' : 'No'}
                                </Typography>
                              </Box>
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  Max Iterations:
                                </Typography>
                                <Typography variant="body2">
                                  {agentPrompts[agent.id].settings.max_iter}
                                </Typography>
                              </Box>
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  Max Execution Time:
                                </Typography>
                                <Typography variant="body2">
                                  {agentPrompts[agent.id].settings.max_execution_time}s
                                </Typography>
                              </Box>
                            </Box>
                          </CardContent>
                        </Card>
                      </Box>
                      
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="h6" gutterBottom color="primary">
                            📖 Background & Instructions
                          </Typography>
                          <Box sx={{ '& p': { mb: 1 }, '& li': { ml: 2 } }}>
                            {formatBackstory(agentPrompts[agent.id].backstory)}
                          </Box>
                        </CardContent>
                      </Card>
                    </Box>
                  ) : (
                    <Button 
                      onClick={() => loadAgentPrompt(agent.id)}
                      variant="outlined"
                      size="small"
                    >
                      Load Configuration
                    </Button>
                  )}
                </Box>
              </Collapse>
            </React.Fragment>
          ))
        )}
      </List>

      {/* System Information */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📊 System Information
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Backend URL:
              </Typography>
              <Typography variant="body2">
                {API_BASE_URL}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Last Check:
              </Typography>
              <Typography variant="body2">
                {formatTimestamp(new Date().toISOString())}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Frontend Version:
              </Typography>
              <Typography variant="body2">
                1.0.0
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Agent Framework:
              </Typography>
              <Typography variant="body2">
                CrewAI + FastAPI
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default AgentManagement;