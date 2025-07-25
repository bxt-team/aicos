import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress
} from '@mui/material';

interface UsageData {
  projects: { current: number; limit: number };
  users: { current: number; limit: number };
  storage: { current_gb: number; limit_gb: number };
  api_calls: { current_month: number };
}

interface OrganizationUsageProps {
  usage: UsageData | null;
  loading: boolean;
}

const OrganizationUsage: React.FC<OrganizationUsageProps> = ({ usage, loading }) => {
  if (loading) {
    return <CircularProgress />;
  }

  if (!usage) {
    return null;
  }

  const usageCards = [
    {
      title: 'Projects',
      value: `${usage.projects.current}/${usage.projects.limit}`,
    },
    {
      title: 'Benutzer',
      value: `${usage.users.current}/${usage.users.limit}`,
    },
    {
      title: 'Speicher (GB)',
      value: `${usage.storage.current_gb}/${usage.storage.limit_gb}`,
    },
    {
      title: 'API-Aufrufe (Monat)',
      value: usage.api_calls.current_month.toLocaleString('de-DE'),
    },
  ];

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Nutzungsstatistik</Typography>
      
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {usageCards.map((card, index) => (
          <Box 
            key={index}
            sx={{ 
              flex: '1 1 100%', 
              '@media (min-width: 900px)': { flex: '1 1 45%' }, 
              '@media (min-width: 1200px)': { flex: '1 1 22%' } 
            }}
          >
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {card.title}
                </Typography>
                <Typography variant="h4">
                  {card.value}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export default OrganizationUsage;