import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Checkbox,
  FormControlLabel,
  TextField,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Card,
  CardContent,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  ArrowBack,
  ArrowForward,
  Send,
  CheckCircle,
  Build,
  People,
  Email,
  Visibility,
} from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  projectId: string;
  onComplete?: () => void;
  onCancel?: () => void;
}

interface TakeoffItem {
  id: string;
  label: string;
  description: string;
  quantity: number;
  unit: string;
}

interface Vendor {
  id: string;
  name: string;
  category: string;
  email: string;
  contact_person?: string;
  rating?: number;
  is_preferred: boolean;
}

const steps = ['Select Items', 'Select Vendors', 'Customize Message', 'Review & Send'];

export default function QuoteRequestForm({ projectId, onComplete, onCancel }: Props) {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [selectedVendors, setSelectedVendors] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [expectedResponseDate, setExpectedResponseDate] = useState('');
  const [items, setItems] = useState<TakeoffItem[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    loadItems();
    loadVendors();

    // Set default expected response date (7 days from now)
    const date = new Date();
    date.setDate(date.getDate() + 7);
    setExpectedResponseDate(date.toISOString().split('T')[0]);

    // Set default message
    setMessage(
      'We are requesting quotes for the following items for our upcoming project. ' +
      'Please provide your best pricing and availability. ' +
      'If you have any questions, please do not hesitate to contact us.'
    );
  }, [projectId]);

  const loadItems = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/takeoffs`);
      setItems(response.data);
    } catch (err) {
      console.error('Failed to load items', err);
    } finally {
      setLoading(false);
    }
  };

  const loadVendors = async () => {
    try {
      const response = await api.get('/vendors', {
        params: { is_active: true },
      });
      setVendors(response.data);
    } catch (err) {
      console.error('Failed to load vendors', err);
    }
  };

  const handleNext = () => {
    if (activeStep === 0 && selectedItems.length === 0) {
      setError('Please select at least one item');
      return;
    }
    if (activeStep === 1 && selectedVendors.length === 0) {
      setError('Please select at least one vendor');
      return;
    }
    setError('');
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleToggleItem = (itemId: string) => {
    setSelectedItems((prev) =>
      prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]
    );
  };

  const handleToggleVendor = (vendorId: string) => {
    setSelectedVendors((prev) =>
      prev.includes(vendorId) ? prev.filter((id) => id !== vendorId) : [...prev, vendorId]
    );
  };

  const handleSend = async () => {
    try {
      setSending(true);
      setError('');

      await api.post(`/projects/${projectId}/quote-requests`, {
        vendor_ids: selectedVendors,
        takeoff_item_ids: selectedItems,
        message: message,
        expected_response_date: expectedResponseDate,
        attach_documents: true,
      });

      setSuccessMessage(
        `Quote requests sent successfully to ${selectedVendors.length} vendor(s) for ${selectedItems.length} item(s)`
      );

      // Wait a moment to show success message
      setTimeout(() => {
        if (onComplete) {
          onComplete();
        }
      }, 2000);
    } catch (err: any) {
      console.error('Failed to send quote requests', err);
      setError(err.response?.data?.detail || 'Failed to send quote requests');
      setSending(false);
    }
  };

  const getSelectedItemsData = () => {
    return items.filter((item) => selectedItems.includes(item.id));
  };

  const getSelectedVendorsData = () => {
    return vendors.filter((vendor) => selectedVendors.includes(vendor.id));
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Select Items to Quote
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Choose the takeoff items you want to request quotes for
            </Typography>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <List>
                {items.map((item) => (
                  <ListItem
                    key={item.id}
                    button
                    onClick={() => handleToggleItem(item.id)}
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1,
                    }}
                  >
                    <ListItemIcon>
                      <Checkbox
                        checked={selectedItems.includes(item.id)}
                        tabIndex={-1}
                        disableRipple
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      secondary={`${item.description} • Quantity: ${item.quantity} ${item.unit}`}
                    />
                  </ListItem>
                ))}
              </List>
            )}

            {selectedItems.length > 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                {selectedItems.length} item(s) selected
              </Alert>
            )}
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Select Vendors
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Choose vendors to send quote requests to
            </Typography>

            <List>
              {vendors.map((vendor) => (
                <ListItem
                  key={vendor.id}
                  button
                  onClick={() => handleToggleVendor(vendor.id)}
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                  }}
                >
                  <ListItemIcon>
                    <Checkbox
                      checked={selectedVendors.includes(vendor.id)}
                      tabIndex={-1}
                      disableRipple
                    />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {vendor.name}
                        {vendor.is_preferred && (
                          <Chip label="Preferred" color="warning" size="small" />
                        )}
                      </Box>
                    }
                    secondary={
                      <>
                        {vendor.category} • {vendor.email}
                        {vendor.contact_person && ` • Contact: ${vendor.contact_person}`}
                      </>
                    }
                  />
                </ListItem>
              ))}
            </List>

            {selectedVendors.length > 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                {selectedVendors.length} vendor(s) selected
              </Alert>
            )}
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Customize Message
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Add a custom message for the vendors
            </Typography>

            <TextField
              label="Message"
              multiline
              rows={6}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              fullWidth
              sx={{ mb: 3 }}
            />

            <TextField
              label="Expected Response Date"
              type="date"
              value={expectedResponseDate}
              onChange={(e) => setExpectedResponseDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
          </Box>
        );

      case 3:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review & Send
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Review your quote request before sending
            </Typography>

            {successMessage && (
              <Alert severity="success" sx={{ mb: 3 }} icon={<CheckCircle />}>
                {successMessage}
              </Alert>
            )}

            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  <Build fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Selected Items ({selectedItems.length})
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Item</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell>Unit</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {getSelectedItemsData().map((item) => (
                        <TableRow key={item.id}>
                          <TableCell>{item.label}</TableCell>
                          <TableCell>{item.description}</TableCell>
                          <TableCell align="right">{item.quantity}</TableCell>
                          <TableCell>{item.unit}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>

            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  <People fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Selected Vendors ({selectedVendors.length})
                </Typography>
                <List dense>
                  {getSelectedVendorsData().map((vendor) => (
                    <ListItem key={vendor.id}>
                      <ListItemText
                        primary={vendor.name}
                        secondary={`${vendor.email} • ${vendor.category}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  <Email fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Message Preview
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body2" paragraph>
                  {message}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Expected Response Date: {new Date(expectedResponseDate).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        {renderStepContent()}
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={activeStep === 0 && onCancel ? onCancel : handleBack}
          disabled={sending}
        >
          {activeStep === 0 ? 'Cancel' : 'Back'}
        </Button>

        {activeStep === steps.length - 1 ? (
          <Button
            variant="contained"
            startIcon={sending ? <CircularProgress size={20} /> : <Send />}
            onClick={handleSend}
            disabled={sending || !!successMessage}
          >
            {sending ? 'Sending...' : 'Send Requests'}
          </Button>
        ) : (
          <Button
            variant="contained"
            endIcon={<ArrowForward />}
            onClick={handleNext}
          >
            Next
          </Button>
        )}
      </Box>
    </Box>
  );
}
