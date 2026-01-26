import { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Tabs,
  Tab,
  Rating,
  InputAdornment,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { Add, Edit, Delete, ArrowBack, Upload, Search, Star } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface Vendor {
  id: string;
  name: string;
  category: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
  contact_person?: string;
  license_number?: string;
  insurance_expiry?: string;
  rating?: number;
  is_preferred: boolean;
  is_active: boolean;
  notes?: string;
}

interface VendorFormData {
  name: string;
  category: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  contact_person: string;
  license_number: string;
  insurance_expiry: string;
  rating: number;
  is_preferred: boolean;
  notes: string;
}

const categoryOptions = [
  { value: 'rental', label: 'Rental' },
  { value: 'subcontractor', label: 'Subcontractor' },
  { value: 'outside_service', label: 'Outside Service' },
  { value: 'material_supplier', label: 'Material Supplier' },
];

export default function VendorSettings() {
  const navigate = useNavigate();
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [openImportDialog, setOpenImportDialog] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [importFile, setImportFile] = useState<File | null>(null);
  const [formData, setFormData] = useState<VendorFormData>({
    name: '',
    category: 'subcontractor',
    email: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    zip: '',
    contact_person: '',
    license_number: '',
    insurance_expiry: '',
    rating: 0,
    is_preferred: false,
    notes: '',
  });

  useEffect(() => {
    fetchVendors();
  }, []);

  const fetchVendors = async () => {
    try {
      setLoading(true);
      const response = await api.get('/vendors');
      setVendors(response.data);
      setError('');
    } catch (err: any) {
      console.error('Failed to fetch vendors', err);
      setError(err.response?.data?.detail || 'Failed to load vendors');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (vendor?: Vendor) => {
    if (vendor) {
      setEditingId(vendor.id);
      setFormData({
        name: vendor.name,
        category: vendor.category,
        email: vendor.email || '',
        phone: vendor.phone || '',
        address: vendor.address || '',
        city: vendor.city || '',
        state: vendor.state || '',
        zip: vendor.zip || '',
        contact_person: vendor.contact_person || '',
        license_number: vendor.license_number || '',
        insurance_expiry: vendor.insurance_expiry || '',
        rating: vendor.rating || 0,
        is_preferred: vendor.is_preferred,
        notes: vendor.notes || '',
      });
    } else {
      setEditingId(null);
      setFormData({
        name: '',
        category: selectedCategory !== 'all' ? selectedCategory : 'subcontractor',
        email: '',
        phone: '',
        address: '',
        city: '',
        state: '',
        zip: '',
        contact_person: '',
        license_number: '',
        insurance_expiry: '',
        rating: 0,
        is_preferred: false,
        notes: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingId(null);
  };

  const handleChange = (field: keyof VendorFormData, value: string | number | boolean) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async () => {
    try {
      const payload = {
        name: formData.name,
        category: formData.category,
        email: formData.email || null,
        phone: formData.phone || null,
        address: formData.address || null,
        city: formData.city || null,
        state: formData.state || null,
        zip: formData.zip || null,
        contact_person: formData.contact_person || null,
        license_number: formData.license_number || null,
        insurance_expiry: formData.insurance_expiry || null,
        rating: formData.rating || null,
        is_preferred: formData.is_preferred,
        is_active: true,
        notes: formData.notes || null,
      };

      if (editingId) {
        await api.put(`/vendors/${editingId}`, payload);
      } else {
        await api.post('/vendors', payload);
      }

      await fetchVendors();
      handleCloseDialog();
      setError('');
      setSuccess(editingId ? 'Vendor updated successfully' : 'Vendor created successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Failed to save vendor', err);
      setError(err.response?.data?.detail || 'Failed to save vendor');
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirmId) return;

    try {
      await api.delete(`/vendors/${deleteConfirmId}`);
      await fetchVendors();
      setDeleteConfirmId(null);
      setError('');
      setSuccess('Vendor deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Failed to delete vendor', err);
      setError(err.response?.data?.detail || 'Failed to delete vendor');
      setDeleteConfirmId(null);
    }
  };

  const handleImportFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setImportFile(event.target.files[0]);
    }
  };

  const handleBulkImport = async () => {
    if (!importFile) return;

    try {
      const formDataUpload = new FormData();
      formDataUpload.append('file', importFile);

      await api.post('/vendors/bulk-import', formDataUpload, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      await fetchVendors();
      setOpenImportDialog(false);
      setImportFile(null);
      setError('');
      setSuccess('Vendors imported successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Failed to import vendors', err);
      setError(err.response?.data?.detail || 'Failed to import vendors');
    }
  };

  const getCategoryChip = (category: string) => {
    const option = categoryOptions.find((opt) => opt.value === category);
    const colorMap: any = {
      rental: 'primary',
      subcontractor: 'secondary',
      outside_service: 'info',
      material_supplier: 'success',
    };
    return (
      <Chip
        label={option?.label || category}
        color={colorMap[category] || 'default'}
        size="small"
      />
    );
  };

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Name',
      flex: 1,
      minWidth: 150,
    },
    {
      field: 'contact_person',
      headerName: 'Contact',
      flex: 1,
      minWidth: 120,
    },
    {
      field: 'email',
      headerName: 'Email',
      flex: 1,
      minWidth: 150,
    },
    {
      field: 'phone',
      headerName: 'Phone',
      width: 130,
    },
    {
      field: 'rating',
      headerName: 'Rating',
      width: 150,
      renderCell: (params: GridRenderCellParams) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Rating value={params.value || 0} readOnly size="small" />
          {params.row.is_preferred && <Chip label="Preferred" size="small" color="warning" />}
        </Box>
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params: GridRenderCellParams) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => handleOpenDialog(params.row)}
            color="primary"
          >
            <Edit fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => setDeleteConfirmId(params.row.id)}
            color="error"
          >
            <Delete fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  const filteredVendors = vendors.filter((vendor) => {
    if (!vendor.is_active) return false;
    if (selectedCategory !== 'all' && vendor.category !== selectedCategory) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        vendor.name.toLowerCase().includes(query) ||
        vendor.email?.toLowerCase().includes(query) ||
        vendor.contact_person?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <IconButton onClick={() => navigate('/dashboard')} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h4">Vendor Management</Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Manage your vendors and supplier contacts
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={selectedCategory}
          onChange={(e, value) => setSelectedCategory(value)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="All Vendors" value="all" />
          <Tab label="Rental" value="rental" />
          <Tab label="Subcontractors" value="subcontractor" />
          <Tab label="Outside Services" value="outside_service" />
          <Tab label="Material Suppliers" value="material_supplier" />
        </Tabs>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => handleOpenDialog()}
          >
            Add Vendor
          </Button>
          <Button
            variant="outlined"
            startIcon={<Upload />}
            onClick={() => setOpenImportDialog(true)}
          >
            Import CSV
          </Button>
          <TextField
            placeholder="Search vendors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            size="small"
            sx={{ minWidth: 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <DataGrid
            rows={filteredVendors}
            columns={columns}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 10 },
              },
            }}
            pageSizeOptions={[5, 10, 25, 50]}
            disableRowSelectionOnClick
            autoHeight
          />
        )}
      </Paper>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingId ? 'Edit Vendor' : 'Add Vendor'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Vendor Name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              required
              fullWidth
            />
            <TextField
              select
              label="Category"
              value={formData.category}
              onChange={(e) => handleChange('category', e.target.value)}
              required
              fullWidth
            >
              {categoryOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Contact Person"
              value={formData.contact_person}
              onChange={(e) => handleChange('contact_person', e.target.value)}
              fullWidth
            />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                fullWidth
              />
              <TextField
                label="Phone"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                fullWidth
              />
            </Box>
            <TextField
              label="Address"
              value={formData.address}
              onChange={(e) => handleChange('address', e.target.value)}
              fullWidth
            />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="City"
                value={formData.city}
                onChange={(e) => handleChange('city', e.target.value)}
                fullWidth
              />
              <TextField
                label="State"
                value={formData.state}
                onChange={(e) => handleChange('state', e.target.value)}
                sx={{ width: '30%' }}
              />
              <TextField
                label="ZIP"
                value={formData.zip}
                onChange={(e) => handleChange('zip', e.target.value)}
                sx={{ width: '30%' }}
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="License Number"
                value={formData.license_number}
                onChange={(e) => handleChange('license_number', e.target.value)}
                fullWidth
              />
              <TextField
                label="Insurance Expiry"
                type="date"
                value={formData.insurance_expiry}
                onChange={(e) => handleChange('insurance_expiry', e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Typography component="legend">Rating</Typography>
              <Rating
                value={formData.rating}
                onChange={(e, value) => handleChange('rating', value || 0)}
              />
              <Box sx={{ flex: 1 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Star color="warning" />
                <Typography variant="body2">Preferred Vendor</Typography>
                <input
                  type="checkbox"
                  checked={formData.is_preferred}
                  onChange={(e) => handleChange('is_preferred', e.target.checked)}
                />
              </Box>
            </Box>
            <TextField
              label="Notes"
              value={formData.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              multiline
              rows={3}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.name || !formData.category}
          >
            {editingId ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={openImportDialog} onClose={() => setOpenImportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Import Vendors from CSV</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <Alert severity="info">
              Upload a CSV file with columns: name, category, email, phone, contact_person, address, city, state, zip
            </Alert>
            <Button
              variant="outlined"
              component="label"
              startIcon={<Upload />}
            >
              {importFile ? importFile.name : 'Select CSV File'}
              <input
                type="file"
                accept=".csv"
                hidden
                onChange={handleImportFile}
              />
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenImportDialog(false)}>Cancel</Button>
          <Button
            onClick={handleBulkImport}
            variant="contained"
            disabled={!importFile}
          >
            Import
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!deleteConfirmId}
        onClose={() => setDeleteConfirmId(null)}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this vendor? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmId(null)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
