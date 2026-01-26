import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Card,
  CardContent,
  Grid,
  Divider,
} from '@mui/material';
import {
  Star,
  TrendingDown,
  TrendingUp,
  CheckCircle,
  CompareArrows,
  Lightbulb,
} from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  projectId: string;
  itemId?: string;
}

interface Quote {
  id: string;
  vendor_id: string;
  vendor_name: string;
  vendor_rating?: number;
  takeoff_item_id: string;
  takeoff_item_label: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  lead_time_days?: number;
  status: string;
  notes?: string;
}

interface ComparisonData {
  item_id: string;
  item_label: string;
  quotes: Quote[];
  lowest_price: number;
  highest_price: number;
  average_price: number;
  price_difference: number;
  recommended_quote_id: string;
  recommendation_reason: string;
}

export default function QuoteComparison({ projectId, itemId }: Props) {
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (itemId) {
      loadComparison();
    }
  }, [projectId, itemId]);

  const loadComparison = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/quotes/compare`, {
        params: itemId ? { item_id: itemId } : undefined,
      });

      // If specific item, get that comparison
      if (itemId && response.data.comparison_by_item) {
        const itemComparison = response.data.comparison_by_item.find(
          (c: any) => c.item_id === itemId
        );
        if (itemComparison) {
          setComparison(itemComparison);
        }
      } else if (response.data.comparison_by_item && response.data.comparison_by_item.length > 0) {
        // Get first item for general comparison
        setComparison(response.data.comparison_by_item[0]);
      }
    } catch (err: any) {
      console.error('Failed to load comparison', err);
      setError(err.response?.data?.detail || 'Failed to load comparison');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (quoteId: string) => {
    try {
      await api.patch(`/projects/${projectId}/quotes/${quoteId}/status`, {
        status: 'accepted',
      });
      setMessage('Quote accepted successfully');
      setTimeout(() => setMessage(''), 3000);
      await loadComparison();
    } catch (err: any) {
      console.error('Failed to accept quote', err);
      setError(err.response?.data?.detail || 'Failed to accept quote');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const calculateSavings = (price: number, lowestPrice: number) => {
    return price - lowestPrice;
  };

  const getStatusChip = (status: string) => {
    const colorMap: any = {
      pending: 'warning',
      accepted: 'success',
      rejected: 'error',
    };
    return <Chip label={status} color={colorMap[status] || 'default'} size="small" />;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" onClose={() => setError('')}>
        {error}
      </Alert>
    );
  }

  if (!comparison || comparison.quotes.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CompareArrows sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          No quotes available for comparison
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Quote Comparison: {comparison.item_label}
      </Typography>

      {message && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <TrendingDown color="success" />
                <Typography variant="caption" color="text.secondary">
                  Lowest Price
                </Typography>
              </Box>
              <Typography variant="h5" color="success.main">
                {formatCurrency(comparison.lowest_price)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <TrendingUp color="error" />
                <Typography variant="caption" color="text.secondary">
                  Highest Price
                </Typography>
              </Box>
              <Typography variant="h5" color="error.main">
                {formatCurrency(comparison.highest_price)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <CompareArrows color="info" />
                <Typography variant="caption" color="text.secondary">
                  Average Price
                </Typography>
              </Box>
              <Typography variant="h5" color="info.main">
                {formatCurrency(comparison.average_price)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Star color="warning" />
                <Typography variant="caption" color="text.secondary">
                  Price Range
                </Typography>
              </Box>
              <Typography variant="h5" color="warning.main">
                {formatCurrency(comparison.price_difference)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recommendation */}
      <Alert severity="info" icon={<Lightbulb />} sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Recommended Quote
        </Typography>
        <Typography variant="body2">{comparison.recommendation_reason}</Typography>
      </Alert>

      {/* Comparison Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Vendor</TableCell>
              <TableCell align="right">Unit Price</TableCell>
              <TableCell align="right">Total Price</TableCell>
              <TableCell align="right">vs. Lowest</TableCell>
              <TableCell align="center">Lead Time</TableCell>
              <TableCell align="center">Rating</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {comparison.quotes
              .sort((a, b) => a.unit_price - b.unit_price)
              .map((quote) => {
                const isLowest = quote.unit_price === comparison.lowest_price;
                const isRecommended = quote.id === comparison.recommended_quote_id;
                const savings = calculateSavings(quote.unit_price, comparison.lowest_price);

                return (
                  <TableRow
                    key={quote.id}
                    sx={{
                      bgcolor: isRecommended
                        ? 'info.lighter'
                        : isLowest
                        ? 'success.lighter'
                        : 'inherit',
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {quote.vendor_name}
                        {isLowest && <Star fontSize="small" color="warning" />}
                        {isRecommended && (
                          <Chip label="Recommended" color="info" size="small" />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography fontWeight={isLowest ? 'bold' : 'normal'}>
                        {formatCurrency(quote.unit_price)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography fontWeight={isLowest ? 'bold' : 'normal'}>
                        {formatCurrency(quote.total_price)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {isLowest ? (
                        <Chip label="Lowest" color="success" size="small" />
                      ) : (
                        <Typography
                          variant="body2"
                          color="error"
                          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}
                        >
                          +{formatCurrency(savings)}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      {quote.lead_time_days ? `${quote.lead_time_days} days` : 'N/A'}
                    </TableCell>
                    <TableCell align="center">
                      {quote.vendor_rating ? (
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 0.5,
                            justifyContent: 'center',
                          }}
                        >
                          <Star fontSize="small" color="warning" />
                          {quote.vendor_rating.toFixed(1)}
                        </Box>
                      ) : (
                        'N/A'
                      )}
                    </TableCell>
                    <TableCell align="center">{getStatusChip(quote.status)}</TableCell>
                    <TableCell align="center">
                      {quote.status === 'pending' && (
                        <Button
                          size="small"
                          variant={isRecommended ? 'contained' : 'outlined'}
                          color="success"
                          startIcon={<CheckCircle />}
                          onClick={() => handleAccept(quote.id)}
                        >
                          Accept
                        </Button>
                      )}
                      {quote.status === 'accepted' && (
                        <Chip
                          icon={<CheckCircle />}
                          label="Accepted"
                          color="success"
                          size="small"
                        />
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Notes Section */}
      <Box sx={{ mt: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Additional Notes
        </Typography>
        {comparison.quotes.map((quote) =>
          quote.notes ? (
            <Paper key={quote.id} sx={{ p: 2, mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {quote.vendor_name}:
              </Typography>
              <Typography variant="body2">{quote.notes}</Typography>
            </Paper>
          ) : null
        )}
      </Box>
    </Box>
  );
}
