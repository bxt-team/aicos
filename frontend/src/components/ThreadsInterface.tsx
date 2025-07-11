import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
} from '@mui/material';
import ThreadsAnalysis from './ThreadsAnalysis';
import ThreadsStrategy from './ThreadsStrategy';
import ThreadsPostManager from './ThreadsPostManager';
import ThreadsSchedule from './ThreadsSchedule';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`threads-tabpanel-${index}`}
      aria-labelledby={`threads-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `threads-tab-${index}`,
    'aria-controls': `threads-tabpanel-${index}`,
  };
}

const ThreadsInterface: React.FC = () => {
  const [value, setValue] = useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Meta Threads Management
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Analyze, strategize, create, and schedule content for Meta Threads
        </Typography>

        <Paper sx={{ width: '100%', mt: 3 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              value={value}
              onChange={handleChange}
              aria-label="threads management tabs"
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab label="Analysis" {...a11yProps(0)} />
              <Tab label="Strategy" {...a11yProps(1)} />
              <Tab label="Post Manager" {...a11yProps(2)} />
              <Tab label="Schedule" {...a11yProps(3)} />
            </Tabs>
          </Box>

          <TabPanel value={value} index={0}>
            <ThreadsAnalysis />
          </TabPanel>
          <TabPanel value={value} index={1}>
            <ThreadsStrategy />
          </TabPanel>
          <TabPanel value={value} index={2}>
            <ThreadsPostManager />
          </TabPanel>
          <TabPanel value={value} index={3}>
            <ThreadsSchedule />
          </TabPanel>
        </Paper>
      </Box>
    </Container>
  );
};

export default ThreadsInterface;