import React, { useEffect, useState } from 'react';
import { 
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import { 
  Receipt as ReceiptIcon,
  Download as DownloadIcon
} from '@mui/icons-material';

interface Payment {
  id: string;
  amount: number;
  currency: string;
  status: string;
  description: string;
  created_at: string;
}

interface Invoice {
  id: string;
  invoice_number: string;
  amount: number;
  currency: string;
  status: string;
  pdf_url: string;
  created_at: string;
}

export const PaymentHistory: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'payments' | 'invoices'>('payments');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      
      // Fetch payments
      const paymentsResponse = await fetch('/api/billing/payments?limit=20', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!paymentsResponse.ok) {
        throw new Error('Failed to fetch payments');
      }

      const paymentsData = await paymentsResponse.json();
      setPayments(paymentsData.payments);

      // Fetch invoices
      const invoicesResponse = await fetch('/api/billing/invoices?limit=20', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!invoicesResponse.ok) {
        throw new Error('Failed to fetch invoices');
      }

      const invoicesData = await invoicesResponse.json();
      setInvoices(invoicesData.invoices);
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
      <Box p={3}>
        <Typography color="error">Error: {error}</Typography>
      </Box>
    );
  }

  const getStatusChip = (status: string) => {
    const statusConfig = {
      succeeded: { color: 'success' as const, label: 'Paid' },
      paid: { color: 'success' as const, label: 'Paid' },
      pending: { color: 'warning' as const, label: 'Pending' },
      failed: { color: 'error' as const, label: 'Failed' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || { 
      color: 'default' as const, 
      label: status 
    };

    return <Chip label={config.label} color={config.color} size="small" />;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase()
    }).format(amount);
  };

  return (
    <Box>
      <Box display="flex" gap={2} mb={3}>
        <Chip 
          label="Payments" 
          onClick={() => setActiveTab('payments')}
          color={activeTab === 'payments' ? 'primary' : 'default'}
        />
        <Chip 
          label="Invoices" 
          onClick={() => setActiveTab('invoices')}
          color={activeTab === 'invoices' ? 'primary' : 'default'}
        />
      </Box>

      {activeTab === 'payments' ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Description</TableCell>
                <TableCell align="right">Amount</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {payments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    <Typography color="text.secondary" py={3}>
                      No payment history available
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                payments.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell>{formatDate(payment.created_at)}</TableCell>
                    <TableCell>{payment.description}</TableCell>
                    <TableCell align="right">
                      {formatCurrency(payment.amount, payment.currency)}
                    </TableCell>
                    <TableCell>{getStatusChip(payment.status)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Invoice #</TableCell>
                <TableCell align="right">Amount</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invoices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography color="text.secondary" py={3}>
                      No invoices available
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                invoices.map((invoice) => (
                  <TableRow key={invoice.id}>
                    <TableCell>{formatDate(invoice.created_at)}</TableCell>
                    <TableCell>{invoice.invoice_number}</TableCell>
                    <TableCell align="right">
                      {formatCurrency(invoice.amount, invoice.currency)}
                    </TableCell>
                    <TableCell>{getStatusChip(invoice.status)}</TableCell>
                    <TableCell align="center">
                      {invoice.pdf_url && (
                        <Tooltip title="Download Invoice">
                          <IconButton 
                            size="small"
                            onClick={() => window.open(invoice.pdf_url, '_blank')}
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};