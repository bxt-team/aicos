import React, { useEffect, useState } from 'react';
import { 
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid
} from '@mui/material';
import { 
  ShoppingCart as CartIcon,
  LocalOffer as OfferIcon
} from '@mui/icons-material';

interface CreditPackage {
  id: string;
  name: string;
  description: string;
  credits: number;
  price: number;
  currency: string;
}

export const CreditPackages: React.FC = () => {
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPackage, setSelectedPackage] = useState<CreditPackage | null>(null);
  const [purchasing, setPurchasing] = useState(false);

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/billing/credit-packages', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch packages');
      }

      const data = await response.json();
      setPackages(data.packages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async () => {
    if (!selectedPackage) return;

    setPurchasing(true);
    try {
      const token = localStorage.getItem('accessToken');
      
      // In a real implementation, this would integrate with Stripe Elements
      // For now, we'll show a message about missing payment method
      alert('Please configure a payment method first. This feature requires Stripe integration.');
      
      // Example purchase request:
      /*
      const response = await fetch('/api/billing/purchase-credits', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          package_id: selectedPackage.id,
          payment_method_id: 'pm_xxx' // From Stripe Elements
        })
      });

      if (!response.ok) {
        throw new Error('Purchase failed');
      }

      alert('Credits purchased successfully!');
      */
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Purchase failed');
    } finally {
      setPurchasing(false);
      setSelectedPackage(null);
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
      <Box p={3}>
        <Typography color="error">Error: {error}</Typography>
      </Box>
    );
  }

  const getCostPerCredit = (price: number, credits: number) => {
    return (price / credits).toFixed(3);
  };

  const getBestValue = () => {
    if (packages.length === 0) return null;
    
    const sorted = [...packages].sort((a, b) => {
      const costA = a.price / a.credits;
      const costB = b.price / b.credits;
      return costA - costB;
    });
    
    return sorted[0].id;
  };

  const bestValueId = getBestValue();

  return (
    <Box>
      <Grid container spacing={3}>
        {packages.map((pkg) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={pkg.id}>
            <Card 
              sx={{ 
                height: '100%',
                position: 'relative',
                border: pkg.id === bestValueId ? '2px solid' : undefined,
                borderColor: 'primary.main'
              }}
            >
              {pkg.id === bestValueId && (
                <Chip 
                  label="Best Value" 
                  color="primary" 
                  size="small"
                  sx={{ 
                    position: 'absolute', 
                    top: 10, 
                    right: 10,
                    zIndex: 1
                  }}
                />
              )}
              
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {pkg.name}
                </Typography>
                
                <Typography variant="h3" color="primary" gutterBottom>
                  {pkg.credits}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  credits
                </Typography>
                
                <Typography variant="h5" gutterBottom sx={{ mt: 2 }}>
                  ${pkg.price}
                </Typography>
                
                <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                  ${getCostPerCredit(pkg.price, pkg.credits)} per credit
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {pkg.description}
                </Typography>
                
                <Button 
                  variant={pkg.id === bestValueId ? "contained" : "outlined"}
                  fullWidth
                  startIcon={<CartIcon />}
                  onClick={() => setSelectedPackage(pkg)}
                >
                  Purchase
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box mt={3} p={2} bgcolor="info.light" borderRadius={1}>
        <Box display="flex" alignItems="center" gap={1}>
          <OfferIcon color="info" />
          <Typography variant="body2">
            <strong>Pro tip:</strong> Larger packages offer better value per credit. 
            Save up to 30% by purchasing in bulk!
          </Typography>
        </Box>
      </Box>

      <Dialog open={!!selectedPackage} onClose={() => setSelectedPackage(null)}>
        <DialogTitle>Confirm Purchase</DialogTitle>
        <DialogContent>
          {selectedPackage && (
            <Box>
              <Typography paragraph>
                You are about to purchase:
              </Typography>
              <Box p={2} bgcolor="grey.100" borderRadius={1}>
                <Typography variant="h6">{selectedPackage.name}</Typography>
                <Typography>{selectedPackage.credits} credits for ${selectedPackage.price}</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Credits will be added to your account immediately after purchase.
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedPackage(null)}>Cancel</Button>
          <Button 
            onClick={handlePurchase} 
            variant="contained" 
            disabled={purchasing}
            startIcon={purchasing ? <CircularProgress size={16} /> : <CartIcon />}
          >
            {purchasing ? 'Processing...' : 'Complete Purchase'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};