import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
} from '@mui/material';
import {
  Add,
  Delete,
  Visibility,
  Send,
  Receipt,
  ShoppingCart,
  Print,
  PictureAsPdf,
} from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  projectId: string;
  onCountUpdate?: (count: number) => void;
}

interface GeneratedQuote {
  id: string;
  quote_number: string;
  quote_date: string;
  expiration_date?: string;
  customer_name?: string;
  customer_company?: string;
  job_name?: string;
  job_reference?: string;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
  status: string;
  line_items?: LineItem[];
  created_at: string;
}

interface LineItem {
  id: string;
  line_number: number;
  category?: string;
  quantity: number;
  unit: string;
  product_code?: string;
  description: string;
  unit_price: number;
  total_price: number;
}

interface TakeoffItem {
  id: string;
  label: string;
  qty: number;
  unit: string;
}

export default function QuotesTab({ projectId, onCountUpdate }: Props) {
  const [activeTab, setActiveTab] = useState(0);
  const [generatedQuotes, setGeneratedQuotes] = useState<GeneratedQuote[]>([]);
  const [takeoffItems, setTakeoffItems] = useState<TakeoffItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [selectedQuote, setSelectedQuote] = useState<GeneratedQuote | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    customer_name: '',
    customer_company: '',
    customer_email: '',
    customer_phone: '',
    delivery_address: '',
    job_name: '',
    tax_rate: '0',
    expiration_days: '7',
    notes: '',
  });

  useEffect(() => {
    loadGeneratedQuotes();
    loadTakeoffItems();
  }, [projectId]);

  const loadGeneratedQuotes = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/generated-quotes`);
      setGeneratedQuotes(response.data.quotes || []);
      if (onCountUpdate) {
        onCountUpdate(response.data.quotes?.length || 0);
      }
    } catch (err) {
      console.error('Failed to load generated quotes', err);
    } finally {
      setLoading(false);
    }
  };

  const loadTakeoffItems = async () => {
    try {
      const response = await api.get(`/projects/${projectId}/takeoffs`);
      setTakeoffItems(response.data || []);
    } catch (err) {
      console.error('Failed to load takeoff items', err);
    }
  };

  const handleGenerateQuote = async () => {
    if (takeoffItems.length === 0) {
      setError('No takeoff items available. Parse a document first to extract items.');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      const response = await api.post(`/projects/${projectId}/generated-quotes/from-takeoffs`, {
        customer_name: generateForm.customer_name || undefined,
        customer_company: generateForm.customer_company || undefined,
        customer_email: generateForm.customer_email || undefined,
        customer_phone: generateForm.customer_phone || undefined,
        delivery_address: generateForm.delivery_address || undefined,
        job_name: generateForm.job_name || undefined,
        tax_rate: parseFloat(generateForm.tax_rate) / 100 || 0,
        expiration_days: parseInt(generateForm.expiration_days) || 7,
        notes: generateForm.notes || undefined,
      });

      setMessage(`Quote #${response.data.quote_number} generated successfully!`);
      setTimeout(() => setMessage(''), 5000);
      setGenerateDialogOpen(false);
      await loadGeneratedQuotes();
      
      // Reset form
      setGenerateForm({
        customer_name: '',
        customer_company: '',
        customer_email: '',
        customer_phone: '',
        delivery_address: '',
        job_name: '',
        tax_rate: '0',
        expiration_days: '7',
        notes: '',
      });
    } catch (err: any) {
      console.error('Failed to generate quote', err);
      setError(err.response?.data?.detail || 'Failed to generate quote');
    } finally {
      setGenerating(false);
    }
  };

  const handleViewQuote = async (quote: GeneratedQuote) => {
    try {
      const response = await api.get(`/projects/${projectId}/generated-quotes/${quote.id}`);
      setSelectedQuote(response.data);
      setViewDialogOpen(true);
    } catch (err) {
      console.error('Failed to load quote details', err);
      setError('Failed to load quote details');
    }
  };

  const handleDeleteQuote = async (quoteId: string) => {
    if (!confirm('Are you sure you want to delete this quote?')) return;

    try {
      await api.delete(`/projects/${projectId}/generated-quotes/${quoteId}`);
      setMessage('Quote deleted successfully');
      setTimeout(() => setMessage(''), 3000);
      await loadGeneratedQuotes();
    } catch (err: any) {
      console.error('Failed to delete quote', err);
      setError(err.response?.data?.detail || 'Failed to delete quote');
    }
  };

  const handleUpdateStatus = async (quoteId: string, newStatus: string) => {
    try {
      await api.put(`/projects/${projectId}/generated-quotes/${quoteId}`, {
        status: newStatus,
      });
      setMessage(`Quote marked as ${newStatus}`);
      setTimeout(() => setMessage(''), 3000);
      await loadGeneratedQuotes();
      setViewDialogOpen(false);
    } catch (err: any) {
      console.error('Failed to update quote status', err);
      setError(err.response?.data?.detail || 'Failed to update quote');
    }
  };

  const handleDownloadPDF = async (quoteId?: string) => {
    const targetQuoteId = quoteId || selectedQuote?.id;
    if (!targetQuoteId) return;

    try {
      setMessage('Generating PDF...');
      const response = await api.post(`/projects/${projectId}/generate-quote-pdf`, {}, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Quote_${selectedQuote?.quote_number || projectId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setMessage('PDF downloaded successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err: any) {
      console.error('Failed to download PDF', err);
      setError(err.response?.data?.detail || 'Failed to generate PDF. Make sure items are matched to catalog.');
    }
  };

  const handlePrintQuote = () => {
    if (!selectedQuote) return;
    
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const lineItemsHtml = selectedQuote.line_items?.map((item, idx) => `
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">${item.quantity} ${item.unit}</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">${item.product_code || '-'}</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">${item.description}</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">$${item.unit_price.toFixed(2)}</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">${item.unit}</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">$${item.total_price.toFixed(2)}</td>
      </tr>
    `).join('') || '';

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Quote #${selectedQuote.quote_number}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          .header { display: flex; justify-content: space-between; margin-bottom: 30px; }
          .quote-info { text-align: right; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th { background: #f5f5f5; padding: 10px; text-align: left; border-bottom: 2px solid #333; }
          .totals { margin-top: 20px; text-align: right; }
          .total-row { font-size: 18px; font-weight: bold; }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <h1>Quotation</h1>
            <p><strong>Customer:</strong> ${selectedQuote.customer_name || 'N/A'}</p>
            <p><strong>Company:</strong> ${selectedQuote.customer_company || 'N/A'}</p>
            <p><strong>Job:</strong> ${selectedQuote.job_name || 'N/A'}</p>
          </div>
          <div class="quote-info">
            <p><strong>Quote No:</strong> ${selectedQuote.quote_number}</p>
            <p><strong>Date:</strong> ${new Date(selectedQuote.quote_date).toLocaleDateString()}</p>
            <p><strong>Expires:</strong> ${selectedQuote.expiration_date ? new Date(selectedQuote.expiration_date).toLocaleDateString() : 'N/A'}</p>
          </div>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Qty/Footage</th>
              <th>Product Code</th>
              <th>Description</th>
              <th style="text-align: right;">Price</th>
              <th>UOM</th>
              <th style="text-align: right;">Total</th>
            </tr>
          </thead>
          <tbody>
            ${lineItemsHtml}
          </tbody>
        </table>
        
        <div class="totals">
          <p>Subtotal: $${selectedQuote.subtotal.toFixed(2)}</p>
          <p>Tax (${(selectedQuote.tax_rate * 100).toFixed(2)}%): $${selectedQuote.tax_amount.toFixed(2)}</p>
          <p class="total-row">Total: $${selectedQuote.total.toFixed(2)}</p>
        </div>
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const getStatusChip = (status: string) => {
    const colorMap: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error'> = {
      draft: 'default',
      sent: 'primary',
      accepted: 'success',
      rejected: 'error',
      expired: 'warning',
    };
    return <Chip label={status} color={colorMap[status] || 'default'} size="small" />;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Quotes</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setGenerateDialogOpen(true)}
            disabled={takeoffItems.length === 0}
          >
            Generate Quote
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

      <Paper>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            icon={<Receipt />}
            label={`Generated Quotes (${generatedQuotes.length})`}
            iconPosition="start"
          />
          <Tab
            icon={<ShoppingCart />}
            label="Vendor Quotes"
            iconPosition="start"
            onClick={() => window.location.href = `#/projects/${projectId}/quotes`}
          />
        </Tabs>

        {activeTab === 0 && (
          <Box sx={{ p: 2 }}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : generatedQuotes.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Receipt sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No quotes generated yet
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {takeoffItems.length === 0
                    ? 'Upload and parse a document first to extract takeoff items'
                    : 'Generate a quote from your takeoff items to send to customers'}
                </Typography>
                {takeoffItems.length > 0 && (
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setGenerateDialogOpen(true)}
                  >
                    Generate Quote
                  </Button>
                )}
              </Box>
            ) : (
              <Grid container spacing={2}>
                {generatedQuotes.map((quote) => (
                  <Grid item xs={12} md={6} lg={4} key={quote.id}>
                    <Card>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="h6">#{quote.quote_number}</Typography>
                          {getStatusChip(quote.status)}
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {quote.customer_name || quote.customer_company || 'No customer'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {quote.job_name || 'No job name'}
                        </Typography>
                        <Divider sx={{ my: 1 }} />
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Date:</Typography>
                          <Typography variant="body2">
                            {new Date(quote.quote_date).toLocaleDateString()}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Items:</Typography>
                          <Typography variant="body2">
                            {quote.line_items?.length || 0}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="subtitle1" fontWeight="bold">Total:</Typography>
                          <Typography variant="subtitle1" fontWeight="bold" color="primary">
                            {formatCurrency(quote.total)}
                          </Typography>
                        </Box>
                        <Divider sx={{ my: 1 }} />
                        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                          <IconButton
                            size="small"
                            onClick={() => handleViewQuote(quote)}
                            title="View"
                          >
                            <Visibility />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleDownloadPDF(quote.id)}
                            title="Download PDF"
                          >
                            <PictureAsPdf />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteQuote(quote.id)}
                            title="Delete"
                          >
                            <Delete />
                          </IconButton>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </Box>
        )}
      </Paper>

      {/* Generate Quote Dialog */}
      <Dialog
        open={generateDialogOpen}
        onClose={() => setGenerateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Generate Quote from Takeoffs</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            This will create a quote with {takeoffItems.length} items from your takeoffs.
            Pricing will be pulled from your material catalog where matches are found.
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Customer Name"
                value={generateForm.customer_name}
                onChange={(e) => setGenerateForm({ ...generateForm, customer_name: e.target.value })}
                fullWidth
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Company"
                value={generateForm.customer_company}
                onChange={(e) => setGenerateForm({ ...generateForm, customer_company: e.target.value })}
                fullWidth
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Email"
                value={generateForm.customer_email}
                onChange={(e) => setGenerateForm({ ...generateForm, customer_email: e.target.value })}
                fullWidth
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Phone"
                value={generateForm.customer_phone}
                onChange={(e) => setGenerateForm({ ...generateForm, customer_phone: e.target.value })}
                fullWidth
                size="small"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Delivery Address"
                value={generateForm.delivery_address}
                onChange={(e) => setGenerateForm({ ...generateForm, delivery_address: e.target.value })}
                fullWidth
                size="small"
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Job Name"
                value={generateForm.job_name}
                onChange={(e) => setGenerateForm({ ...generateForm, job_name: e.target.value })}
                fullWidth
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                label="Tax Rate (%)"
                value={generateForm.tax_rate}
                onChange={(e) => setGenerateForm({ ...generateForm, tax_rate: e.target.value })}
                fullWidth
                size="small"
                type="number"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                label="Valid Days"
                value={generateForm.expiration_days}
                onChange={(e) => setGenerateForm({ ...generateForm, expiration_days: e.target.value })}
                fullWidth
                size="small"
                type="number"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Notes"
                value={generateForm.notes}
                onChange={(e) => setGenerateForm({ ...generateForm, notes: e.target.value })}
                fullWidth
                size="small"
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenerateDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleGenerateQuote}
            disabled={generating}
            startIcon={generating ? <CircularProgress size={16} /> : <Add />}
          >
            {generating ? 'Generating...' : 'Generate Quote'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Quote Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              Quote #{selectedQuote?.quote_number}
              <Box component="span" sx={{ ml: 2 }}>
                {selectedQuote && getStatusChip(selectedQuote.status)}
              </Box>
            </Box>
            <Box>
              <IconButton onClick={() => handleDownloadPDF()} title="Download PDF">
                <PictureAsPdf />
              </IconButton>
              <IconButton onClick={handlePrintQuote} title="Print">
                <Print />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedQuote && (
            <>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">Customer</Typography>
                  <Typography>{selectedQuote.customer_name || 'N/A'}</Typography>
                  <Typography>{selectedQuote.customer_company || ''}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">Job</Typography>
                  <Typography>{selectedQuote.job_name || 'N/A'}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ref: {selectedQuote.job_reference || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="text.secondary">Quote Date</Typography>
                  <Typography>{new Date(selectedQuote.quote_date).toLocaleDateString()}</Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="text.secondary">Expires</Typography>
                  <Typography>
                    {selectedQuote.expiration_date
                      ? new Date(selectedQuote.expiration_date).toLocaleDateString()
                      : 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                  {getStatusChip(selectedQuote.status)}
                </Grid>
              </Grid>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.100' }}>
                      <TableCell>Qty/Footage</TableCell>
                      <TableCell>Product Code</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell>UOM</TableCell>
                      <TableCell align="right">Total</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {selectedQuote.line_items?.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.quantity}</TableCell>
                        <TableCell>{item.product_code || '-'}</TableCell>
                        <TableCell>{item.description}</TableCell>
                        <TableCell align="right">{formatCurrency(item.unit_price)}</TableCell>
                        <TableCell>{item.unit}</TableCell>
                        <TableCell align="right">{formatCurrency(item.total_price)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Box sx={{ mt: 2, textAlign: 'right' }}>
                <Typography variant="body1">
                  Subtotal: {formatCurrency(selectedQuote.subtotal)}
                </Typography>
                <Typography variant="body1">
                  Tax ({(selectedQuote.tax_rate * 100).toFixed(2)}%): {formatCurrency(selectedQuote.tax_amount)}
                </Typography>
                <Typography variant="h6" fontWeight="bold" color="primary">
                  Total: {formatCurrency(selectedQuote.total)}
                </Typography>
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          {selectedQuote?.status === 'draft' && (
            <>
              <Button
                color="primary"
                startIcon={<Send />}
                onClick={() => handleUpdateStatus(selectedQuote.id, 'sent')}
              >
                Mark as Sent
              </Button>
            </>
          )}
          {selectedQuote?.status === 'sent' && (
            <>
              <Button
                color="success"
                onClick={() => handleUpdateStatus(selectedQuote.id, 'accepted')}
              >
                Mark Accepted
              </Button>
              <Button
                color="error"
                onClick={() => handleUpdateStatus(selectedQuote.id, 'rejected')}
              >
                Mark Rejected
              </Button>
            </>
          )}
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
