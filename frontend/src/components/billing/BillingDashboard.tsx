import React from 'react';
import { 
  Container, 
  Typography, 
  Box,
  Tab,
  Tabs,
  Paper,
  Grid
} from '@mui/material';
import { CreditBalance } from './CreditBalance';
import { SubscriptionCard } from './SubscriptionCard';
import { CreditUsageChart } from './CreditUsageChart';
import { PaymentHistory } from './PaymentHistory';
import { CreditPackages } from './CreditPackages';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`billing-tabpanel-${index}`}
      aria-labelledby={`billing-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

export const BillingDashboard: React.FC = () => {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg">
      <Box py={3}>
        <Typography variant="h4" gutterBottom>
          Billing & Credits
        </Typography>
        
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, lg: 6 }}>
            <CreditBalance />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <SubscriptionCard />
          </Grid>
        </Grid>

        <Paper sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange} 
              aria-label="billing tabs"
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab label="Usage Analytics" />
              <Tab label="Purchase Credits" />
              <Tab label="Payment History" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <CreditUsageChart />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <CreditPackages />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <PaymentHistory />
          </TabPanel>
        </Paper>
      </Box>
    </Container>
  );
};