import React, { useState } from 'react';
import { Box, Tabs, Tab, Typography, Paper } from '@mui/material';
import XAnalysis from './XAnalysis';
import XStrategy from './XStrategy';
import XPostManager from './XPostManager';
import XSchedule from './XSchedule';

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
      id={`x-tabpanel-${index}`}
      aria-labelledby={`x-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `x-tab-${index}`,
    'aria-controls': `x-tabpanel-${index}`,
  };
}

const XInterface: React.FC = () => {
  const [value, setValue] = useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper elevation={3} sx={{ mb: 3, p: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          X (Twitter) Content Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your X presence with AI-powered content creation and scheduling
        </Typography>
      </Paper>

      <Paper elevation={1}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={value} 
            onChange={handleChange} 
            aria-label="X management tabs"
            variant="fullWidth"
          >
            <Tab label="Analysis" {...a11yProps(0)} />
            <Tab label="Strategy" {...a11yProps(1)} />
            <Tab label="Post Manager" {...a11yProps(2)} />
            <Tab label="Schedule" {...a11yProps(3)} />
          </Tabs>
        </Box>

        <TabPanel value={value} index={0}>
          <XAnalysis />
        </TabPanel>
        <TabPanel value={value} index={1}>
          <XStrategy />
        </TabPanel>
        <TabPanel value={value} index={2}>
          <XPostManager />
        </TabPanel>
        <TabPanel value={value} index={3}>
          <XSchedule />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default XInterface;