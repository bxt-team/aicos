import React, { useEffect, useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Button,
  Chip,
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import { 
  CreditCard as CreditCardIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Update as UpdateIcon
} from '@mui/icons-material';

interface SubscriptionData {
  id: string;
  status: string;
  plan: {
    id: string;
    name: string;
    price: number;
    interval: string;
    included_credits: number;
  };
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

export const SubscriptionCard: React.FC = () => {
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSubscription();
  }, []);

  const fetchSubscription = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/billing/subscription', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch subscription');
      }

      const data = await response.json();
      setSubscription(data.subscription);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!window.confirm('Are you sure you want to cancel your subscription?')) {
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/billing/subscription', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to cancel subscription');
      }

      // Refresh subscription data
      await fetchSubscription();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to cancel subscription');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Typography color="error">Error: {error}</Typography>
        </CardContent>
      </Card>
    );
  }

  if (!subscription) {
    return (
      <Card>
        <CardContent>
          <Box textAlign="center" py={3}>
            <Typography variant="h6" gutterBottom>
              No Active Subscription
            </Typography>
            <Typography color="text.secondary" paragraph>
              Subscribe to a plan to get monthly credits and unlock all features.
            </Typography>
            <Button 
              variant="contained" 
              color="primary" 
              href="/billing/plans"
              startIcon={<CreditCardIcon />}
            >
              View Plans
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const nextBillingDate = new Date(subscription.current_period_end).toLocaleDateString();
  const statusColor = subscription.status === 'active' ? 'success' : 'warning';

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
          <Box display="flex" alignItems="center" gap={1}>
            <CreditCardIcon color="primary" />
            <Typography variant="h6">Current Subscription</Typography>
          </Box>
          <Chip 
            label={subscription.status} 
            color={statusColor} 
            size="small"
          />
        </Box>

        <Box mb={3}>
          <Typography variant="h5" gutterBottom>
            {subscription.plan.name}
          </Typography>
          <Typography variant="h4" color="primary" gutterBottom>
            ${subscription.plan.price} / {subscription.plan.interval}
          </Typography>
          <Typography color="text.secondary">
            {subscription.plan.included_credits} credits included monthly
          </Typography>
        </Box>

        <Box mb={3}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Next billing date
          </Typography>
          <Typography variant="body1">
            {nextBillingDate}
          </Typography>
          {subscription.cancel_at_period_end && (
            <Chip 
              label="Cancels at period end" 
              color="warning" 
              size="small" 
              sx={{ mt: 1 }}
            />
          )}
        </Box>

        <Box display="flex" gap={2}>
          <Button 
            variant="outlined" 
            startIcon={<UpdateIcon />}
            href="/billing/plans"
          >
            Change Plan
          </Button>
          {!subscription.cancel_at_period_end && (
            <Button 
              variant="outlined" 
              color="error"
              startIcon={<CancelIcon />}
              onClick={handleCancelSubscription}
            >
              Cancel Subscription
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};