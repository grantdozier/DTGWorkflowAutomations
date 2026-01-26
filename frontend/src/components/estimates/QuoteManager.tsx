import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  TextField,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Add,
  CheckCircle,
  Cancel,
  Visibility,
  Star,
  TrendingDown,
  Compare,
  ShoppingCart,
} from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  projectId: string;
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
  created_at: string;
}

interface GroupedQuotes {
  [itemId: string]: {
    item_label: string;
    quotes: Quote[];
  };
}

export default function QuoteManager({ projectId }: Props) {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [groupedQuotes, setGroupedQuotes] = useState<GroupedQuotes>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [filterVendor, setFilterVendor] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterItem, setFilterItem] = useState('all');
  const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null);
  const [compareDialogOpen, setCompareDialogOpen] = useState(false);
  const [compareItemId, setCompareItemId] = useState<string | null>(null);
  const [vendors, setVendors] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    loadQuotes();
    loadVendors();
    loadItems();
  }, [projectId]);

  const loadQuotes = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/quotes`);
      setQuotes(response.data);
      groupQuotesByItem(response.data);
    } catch (err) {
      console.error('Failed to load quotes', err);
    } finally {
      setLoading(false);
    }
  };

  const loadVendors = async () => {
    try {
      const response = await api.get('/vendors');
      setVendors(response.data);
    } catch (err) {
      console.error('Failed to load vendors', err);
    }
  };

  const loadItems = async () => {
    try {
      const response = await api.get(`/projects/${projectId}/takeoffs`);
      setItems(response.data);
    } catch (err) {
      console.error('Failed to load items', err);
    }
  };

  const groupQuotesByItem = (quotesData: Quote[]) => {
    const grouped: GroupedQuotes = {};
    quotesData.forEach((quote) => {
      if (!grouped[quote.takeoff_item_id]) {
        grouped[quote.takeoff_item_id] = {
          item_label: quote.takeoff_item_label,
          quotes: [],
        };
      }
      grouped[quote.takeoff_item_id].quotes.push(quote);
    });
    setGroupedQuotes(grouped);
  };

  const handleAccept = async (quoteId: string) => {
    try {
      await api.patch(`/projects/${projectId}/quotes/${quoteId}/status`, {
        status: 'accepted',
      });
      setMessage('Quote accepted successfully');
      setTimeout(() => setMessage(''), 3000);
      await loadQuotes();
    } catch (err: any) {
      console.error('Failed to accept quote', err);
      setError(err.response?.data?.detail || 'Failed to accept quote');
    }
  };

  const handleReject = async (quoteId: string) => {
    try {
      await api.patch(`/projects/${projectId}/quotes/${quoteId}/status`, {
        status: 'rejected',
      });
      setMessage('Quote rejected');
      setTimeout(() => setMessage(''), 3000);
      await loadQuotes();
    } catch (err: any) {
      console.error('Failed to reject quote', err);
      setError(err.response?.data?.detail || 'Failed to reject quote');
    }
  };

  const handleCompare = (itemId: string) => {
    setCompareItemId(itemId);
    setCompareDialogOpen(true);
  };

  const getStatusChip = (status: string) => {
    const colorMap: any = {
      pending: 'warning',
      accepted: 'success',
      rejected: 'error',
      expired: 'default',
    };
    return <Chip label={status} color={colorMap[status] || 'default'} size="small" />;
  };

  const getLowestPrice = (quotes: Quote[]) => {
    return Math.min(...quotes.map((q) => q.unit_price));
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const filteredQuotes = quotes.filter((quote) => {
    if (filterVendor !== 'all' && quote.vendor_id !== filterVendor) return false;
    if (filterStatus !== 'all' && quote.status !== filterStatus) return false;
    if (filterItem !== 'all' && quote.takeoff_item_id !== filterItem) return false;
    return true;
  });

  const filteredGrouped: GroupedQuotes = {};
  Object.keys(groupedQuotes).forEach((itemId) => {
    const filtered = groupedQuotes[itemId].quotes.filter((quote) => {
      if (filterVendor !== 'all' && quote.vendor_id !== filterVendor) return false;
      if (filterStatus !== 'all' && quote.status !== filterStatus) return false;
      return true;
    });
    if (filtered.length > 0) {
      filteredGrouped[itemId] = {
        item_label: groupedQuotes[itemId].item_label,
        quotes: filtered,
      };
    }
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Quote Management</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Compare />}
            onClick={() => setCompareDialogOpen(true)}
            disabled={Object.keys(groupedQuotes).length === 0}
          >
            Compare All
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => {
              // Navigate to quote request form
              window.location.href = `#/projects/${projectId}/request-quotes`;
            }}
          >
            Request Quotes
          </Button>
        </Box>
      </Box>

      {message && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <TextField
              select
              label="Filter by Item"
              value={filterItem}
              onChange={(e) => setFilterItem(e.target.value)}
              size="small"
              fullWidth
            >
              <MenuItem value="all">All Items</MenuItem>
              {items.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.label}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              select
              label="Filter by Vendor"
              value={filterVendor}
              onChange={(e) => setFilterVendor(e.target.value)}
              size="small"
              fullWidth
            >
              <MenuItem value="all">All Vendors</MenuItem>
              {vendors.map((vendor) => (
                <MenuItem key={vendor.id} value={vendor.id}>
                  {vendor.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              select
              label="Filter by Status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              size="small"
              fullWidth
            >
              <MenuItem value="all">All Statuses</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="accepted">Accepted</MenuItem>
              <MenuItem value="rejected">Rejected</MenuItem>
            </TextField>
          </Grid>
        </Grid>
      </Paper>

      {/* Quotes Grouped by Item */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : Object.keys(filteredGrouped).length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <ShoppingCart sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No quotes available
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Request quotes from vendors to get started
          </Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => {
              window.location.href = `#/projects/${projectId}/request-quotes`;
            }}
          >
            Request Quotes
          </Button>
        </Paper>
      ) : (
        <Box>
          {Object.entries(filteredGrouped).map(([itemId, data]) => {
            const lowestPrice = getLowestPrice(data.quotes);
            return (
              <Card key={itemId} sx={{ mb: 3 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Box>
                      <Typography variant="h6">{data.item_label}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {data.quotes.length} quotes received
                      </Typography>
                    </Box>
                    <Button
                      size="small"
                      startIcon={<Compare />}
                      onClick={() => handleCompare(itemId)}
                    >
                      Compare
                    </Button>
                  </Box>

                  <Grid container spacing={2}>
                    {data.quotes.map((quote) => (
                      <Grid item xs={12} md={6} key={quote.id}>
                        <Paper
                          sx={{
                            p: 2,
                            border: quote.unit_price === lowestPrice ? '2px solid' : '1px solid',
                            borderColor: quote.unit_price === lowestPrice ? 'success.main' : 'divider',
                            position: 'relative',
                          }}
                        >
                          {quote.unit_price === lowestPrice && (
                            <Chip
                              icon={<Star />}
                              label="Lowest Price"
                              color="success"
                              size="small"
                              sx={{ position: 'absolute', top: 8, right: 8 }}
                            />
                          )}
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Box>
                              <Typography variant="subtitle1" fontWeight="bold">
                                {quote.vendor_name}
                              </Typography>
                              {quote.vendor_rating && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <Star fontSize="small" color="warning" />
                                  <Typography variant="caption">
                                    {quote.vendor_rating.toFixed(1)}
                                  </Typography>
                                </Box>
                              )}
                            </Box>
                            {getStatusChip(quote.status)}
                          </Box>

                          <Divider sx={{ my: 1 }} />

                          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 2 }}>
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Unit Price
                              </Typography>
                              <Typography variant="h6" color="primary">
                                {formatCurrency(quote.unit_price)}
                              </Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Total
                              </Typography>
                              <Typography variant="h6" color="primary">
                                {formatCurrency(quote.total_price)}
                              </Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Quantity
                              </Typography>
                              <Typography variant="body2">
                                {quote.quantity} {quote.unit}
                              </Typography>
                            </Box>
                            {quote.lead_time_days && (
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  Lead Time
                                </Typography>
                                <Typography variant="body2">
                                  {quote.lead_time_days} days
                                </Typography>
                              </Box>
                            )}
                          </Box>

                          {quote.notes && (
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                              {quote.notes}
                            </Typography>
                          )}

                          {quote.status === 'pending' && (
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Button
                                variant="contained"
                                color="success"
                                size="small"
                                startIcon={<CheckCircle />}
                                onClick={() => handleAccept(quote.id)}
                                fullWidth
                              >
                                Accept
                              </Button>
                              <Button
                                variant="outlined"
                                color="error"
                                size="small"
                                startIcon={<Cancel />}
                                onClick={() => handleReject(quote.id)}
                                fullWidth
                              >
                                Reject
                              </Button>
                            </Box>
                          )}
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      )}

      {/* Compare Dialog */}
      <Dialog
        open={compareDialogOpen}
        onClose={() => setCompareDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Compare Quotes</DialogTitle>
        <DialogContent>
          {compareItemId && groupedQuotes[compareItemId] ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Vendor</TableCell>
                    <TableCell align="right">Unit Price</TableCell>
                    <TableCell align="right">Total Price</TableCell>
                    <TableCell align="right">Lead Time</TableCell>
                    <TableCell align="center">Rating</TableCell>
                    <TableCell align="center">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {groupedQuotes[compareItemId].quotes.map((quote) => {
                    const isLowest = quote.unit_price === getLowestPrice(groupedQuotes[compareItemId].quotes);
                    return (
                      <TableRow
                        key={quote.id}
                        sx={{
                          bgcolor: isLowest ? 'success.lighter' : 'inherit',
                        }}
                      >
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {quote.vendor_name}
                            {isLowest && <Star fontSize="small" color="warning" />}
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
                          {quote.lead_time_days ? `${quote.lead_time_days} days` : 'N/A'}
                        </TableCell>
                        <TableCell align="center">
                          {quote.vendor_rating ? (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'center' }}>
                              <Star fontSize="small" color="warning" />
                              {quote.vendor_rating.toFixed(1)}
                            </Box>
                          ) : (
                            'N/A'
                          )}
                        </TableCell>
                        <TableCell align="center">{getStatusChip(quote.status)}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography>Select an item to compare quotes</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompareDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
