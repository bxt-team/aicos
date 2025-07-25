import React, { useEffect, useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  CircularProgress,
  Button,
  Chip
} from '@mui/material';
import { 
  AccountBalanceWallet as WalletIcon,
  TrendingUp as TrendingIcon,
  ShoppingCart as CartIcon
} from '@mui/icons-material';
import { useSupabaseAuth } from '../../contexts/SupabaseAuthContext';

interface CreditBalanceData {
  available: number;
  reserved?: number;
  total_purchased: number;
  total_consumed: number;
  updated_at: string;
}

export const CreditBalance: React.FC = () => {
  const { user } = useSupabaseAuth();
  const [balance, setBalance] = useState<CreditBalanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBalance();
  }, []);

  const fetchBalance = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/credits/balance', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch balance');
      }

      const data = await response.json();
      setBalance(data.balance);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
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

  const getBalanceColor = (credits: number) => {
    if (credits < 10) return 'error';
    if (credits < 50) return 'warning';
    return 'success';
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <WalletIcon color="primary" />
            <Typography variant="h6">Credit Balance</Typography>
          </Box>
          <Button 
            variant="contained" 
            size="small" 
            startIcon={<CartIcon />}
            href="/billing/purchase"
          >
            Buy Credits
          </Button>
        </Box>

        <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={3}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Available Credits
            </Typography>
            <Box display="flex" alignItems="baseline" gap={1}>
              <Typography variant="h4" component="span">
                {balance?.available.toFixed(0) || 0}
              </Typography>
              <Chip 
                label={getBalanceColor(balance?.available || 0)} 
                color={getBalanceColor(balance?.available || 0)} 
                size="small" 
              />
            </Box>
          </Box>

          {balance?.reserved && balance.reserved > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Reserved
              </Typography>
              <Typography variant="h4">
                {balance.reserved.toFixed(0)}
              </Typography>
            </Box>
          )}

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total Consumed
            </Typography>
            <Box display="flex" alignItems="center" gap={0.5}>
              <TrendingIcon fontSize="small" color="action" />
              <Typography variant="h5">
                {balance?.total_consumed.toFixed(0) || 0}
              </Typography>
            </Box>
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total Purchased
            </Typography>
            <Typography variant="h5">
              {balance?.total_purchased.toFixed(0) || 0}
            </Typography>
          </Box>
        </Box>

        {balance && balance.available < 50 && (
          <Box mt={2} p={2} bgcolor="warning.light" borderRadius={1}>
            <Typography variant="body2" color="warning.dark">
              ⚠️ Your credit balance is running low. Consider purchasing more credits to avoid interruptions.
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};