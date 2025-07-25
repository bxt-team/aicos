import React, { useEffect, useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  CircularProgress,
  FormControl,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material';
import { BarChart as ChartIcon } from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

interface UsageSummary {
  key: string;
  total_credits: number;
  action_count: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export const CreditUsageChart: React.FC = () => {
  const [data, setData] = useState<UsageSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [groupBy, setGroupBy] = useState<string>('agent');
  const [timeRange, setTimeRange] = useState<number>(7); // days

  useEffect(() => {
    fetchUsageData();
  }, [groupBy, timeRange]);

  const fetchUsageData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - timeRange);

      const params = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        group_by: groupBy
      });

      const response = await fetch(`/api/credits/usage/summary?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch usage data');
      }

      const result = await response.json();
      setData(result.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleGroupByChange = (event: SelectChangeEvent) => {
    setGroupBy(event.target.value);
  };

  const handleTimeRangeChange = (event: SelectChangeEvent<number>) => {
    setTimeRange(event.target.value as number);
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

  const chartData = data.slice(0, 10).map(item => ({
    name: item.key,
    credits: item.total_credits,
    actions: item.action_count
  }));

  const pieData = data.slice(0, 6).map(item => ({
    name: item.key,
    value: item.total_credits
  }));

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
          <Box display="flex" alignItems="center" gap={1}>
            <ChartIcon color="primary" />
            <Typography variant="h6">Credit Usage Analytics</Typography>
          </Box>
          
          <Box display="flex" gap={2}>
            <FormControl size="small">
              <Select value={timeRange} onChange={handleTimeRangeChange}>
                <MenuItem value={1}>Last 24 hours</MenuItem>
                <MenuItem value={7}>Last 7 days</MenuItem>
                <MenuItem value={30}>Last 30 days</MenuItem>
                <MenuItem value={90}>Last 90 days</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl size="small">
              <Select value={groupBy} onChange={handleGroupByChange}>
                <MenuItem value="agent">By Agent</MenuItem>
                <MenuItem value="day">By Day</MenuItem>
                <MenuItem value="project">By Project</MenuItem>
                <MenuItem value="department">By Department</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>

        {data.length === 0 ? (
          <Box textAlign="center" py={5}>
            <Typography color="text.secondary">
              No usage data available for the selected period
            </Typography>
          </Box>
        ) : (
          <>
            {groupBy === 'agent' ? (
              <Box display="grid" gridTemplateColumns={{ xs: '1fr', md: '1fr 1fr' }} gap={3}>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Credits by {groupBy}
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="credits" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }: { name: string; percent: number }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </Box>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="credits" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            )}

            <Box mt={3} p={2} bgcolor="grey.100" borderRadius={1}>
              <Typography variant="body2" color="text.secondary">
                Total credits consumed: {data.reduce((sum, item) => sum + item.total_credits, 0).toFixed(0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total actions performed: {data.reduce((sum, item) => sum + item.action_count, 0)}
              </Typography>
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};