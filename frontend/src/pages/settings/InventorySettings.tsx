import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Tooltip,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Search,
  Refresh,
  Inventory,
} from '@mui/icons-material';
import api from '../../services/api';

interface Material {
  id: string;
  product_code: string;
  description: string;
  category: string;
  unit_price: number;
  unit: string;
  manufacturer?: string;
  specifications?: string;
  notes?: string;
  is_active: boolean;
  lead_time_days?: number;
  minimum_order?: number;
}

interface Props {
  onMessage?: (msg: string, severity: 'success' | 'error') => void;
}

export default function InventorySettings({ onMessage }: Props) {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editMaterial, setEditMaterial] = useState<Material | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadMaterials();
    loadCategories();
  }, [categoryFilter, showInactive]);

  const loadMaterials = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (categoryFilter) params.append('category', categoryFilter);
      if (searchTerm) params.append('search', searchTerm);
      params.append('is_active', showInactive ? 'false' : 'true');
      params.append('limit', '500');
      
      const response = await api.get(`/materials/?${params.toString()}`);
      setMaterials(response.data || []);
    } catch (err) {
      console.error('Failed to load materials', err);
      onMessage?.('Failed to load materials', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await api.get('/materials/categories');
      setCategories(response.data.categories || []);
    } catch (err) {
      console.error('Failed to load categories', err);
    }
  };

  const handleSearch = () => {
    loadMaterials();
  };

  const handleRescrape = async () => {
    try {
      setScraping(true);
      onMessage?.('Starting material scrape from web sources...', 'success');
      
      const response = await api.post('/import/scrape-materials');
      
      onMessage?.(`Scrape complete! ${response.data.imported_count || 0} materials imported.`, 'success');
      await loadMaterials();
      await loadCategories();
    } catch (err: any) {
      console.error('Failed to scrape materials', err);
      onMessage?.(err.response?.data?.detail || 'Failed to scrape materials', 'error');
    } finally {
      setScraping(false);
    }
  };

  const handleEditClick = (material: Material) => {
    setEditMaterial({ ...material });
    setEditDialogOpen(true);
  };

  const handleAddNew = () => {
    setEditMaterial({
      id: '',
      product_code: '',
      description: '',
      category: '',
      unit_price: 0,
      unit: 'EA',
      manufacturer: '',
      specifications: '',
      notes: '',
      is_active: true,
      lead_time_days: undefined,
      minimum_order: undefined,
    });
    setEditDialogOpen(true);
  };

  const handleSaveMaterial = async () => {
    if (!editMaterial) return;

    try {
      setSaving(true);

      if (editMaterial.id) {
        await api.put(`/materials/${editMaterial.id}`, {
          product_code: editMaterial.product_code,
          description: editMaterial.description,
          category: editMaterial.category,
          unit_price: editMaterial.unit_price,
          unit: editMaterial.unit,
          manufacturer: editMaterial.manufacturer,
          specifications: editMaterial.specifications,
          notes: editMaterial.notes,
          is_active: editMaterial.is_active,
          lead_time_days: editMaterial.lead_time_days,
          minimum_order: editMaterial.minimum_order,
        });
        onMessage?.('Material updated successfully', 'success');
      } else {
        await api.post('/materials/', {
          product_code: editMaterial.product_code,
          description: editMaterial.description,
          category: editMaterial.category,
          unit_price: editMaterial.unit_price,
          unit: editMaterial.unit,
          manufacturer: editMaterial.manufacturer,
          specifications: editMaterial.specifications,
          notes: editMaterial.notes,
          is_active: editMaterial.is_active,
          lead_time_days: editMaterial.lead_time_days,
          minimum_order: editMaterial.minimum_order,
        });
        onMessage?.('Material created successfully', 'success');
      }

      setEditDialogOpen(false);
      setEditMaterial(null);
      await loadMaterials();
    } catch (err: any) {
      console.error('Failed to save material', err);
      onMessage?.(err.response?.data?.detail || 'Failed to save material', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteMaterial = async (materialId: string) => {
    if (!confirm('Are you sure you want to deactivate this material?')) return;

    try {
      await api.delete(`/materials/${materialId}`);
      onMessage?.('Material deactivated', 'success');
      await loadMaterials();
    } catch (err: any) {
      console.error('Failed to delete material', err);
      onMessage?.(err.response?.data?.detail || 'Failed to delete material', 'error');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h6" fontWeight="bold">
            Material Inventory
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {materials.length} materials in catalog
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={scraping ? <CircularProgress size={16} /> : <Refresh />}
            onClick={handleRescrape}
            disabled={scraping}
          >
            {scraping ? 'Scraping...' : 'Rescrape from Web'}
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleAddNew}
          >
            Add Material
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search by code or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="">All Categories</MenuItem>
                {categories.map((cat) => (
                  <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={2}>
            <Button
              variant={showInactive ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setShowInactive(!showInactive)}
              fullWidth
            >
              {showInactive ? 'Showing Inactive' : 'Show Inactive'}
            </Button>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button
              variant="contained"
              startIcon={<Search />}
              onClick={handleSearch}
              fullWidth
            >
              Search
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Materials Table */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : materials.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Inventory sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No materials found
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {searchTerm || categoryFilter
              ? 'Try adjusting your search filters'
              : 'Add materials manually or scrape from web sources'}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
            <Button variant="outlined" onClick={handleRescrape} disabled={scraping}>
              Scrape from Web
            </Button>
            <Button variant="contained" onClick={handleAddNew}>
              Add Material
            </Button>
          </Box>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: 'grey.100' }}>
                <TableCell>Product Code</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Category</TableCell>
                <TableCell align="right">Unit Price</TableCell>
                <TableCell>Unit</TableCell>
                <TableCell>Manufacturer</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {materials.map((material) => (
                <TableRow key={material.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {material.product_code}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Tooltip title={material.description}>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 250 }}>
                        {material.description}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Chip label={material.category} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" fontWeight="medium">
                      {formatCurrency(material.unit_price)}
                    </Typography>
                  </TableCell>
                  <TableCell>{material.unit}</TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {material.manufacturer || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={material.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={material.is_active ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton size="small" onClick={() => handleEditClick(material)}>
                      <Edit fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteMaterial(material.id)}
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Edit/Add Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editMaterial?.id ? 'Edit Material' : 'Add New Material'}
        </DialogTitle>
        <DialogContent>
          {editMaterial && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Product Code"
                  value={editMaterial.product_code}
                  onChange={(e) => setEditMaterial({ ...editMaterial, product_code: e.target.value })}
                  fullWidth
                  required
                />
              </Grid>
              <Grid item xs={12} sm={8}>
                <TextField
                  label="Description"
                  value={editMaterial.description}
                  onChange={(e) => setEditMaterial({ ...editMaterial, description: e.target.value })}
                  fullWidth
                  required
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Category"
                  value={editMaterial.category}
                  onChange={(e) => setEditMaterial({ ...editMaterial, category: e.target.value })}
                  fullWidth
                  required
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Unit Price"
                  type="number"
                  value={editMaterial.unit_price}
                  onChange={(e) => setEditMaterial({ ...editMaterial, unit_price: parseFloat(e.target.value) || 0 })}
                  fullWidth
                  required
                  InputProps={{
                    startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Unit"
                  value={editMaterial.unit}
                  onChange={(e) => setEditMaterial({ ...editMaterial, unit: e.target.value })}
                  fullWidth
                  required
                  placeholder="EA, LF, BDL, etc."
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Manufacturer"
                  value={editMaterial.manufacturer || ''}
                  onChange={(e) => setEditMaterial({ ...editMaterial, manufacturer: e.target.value })}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  label="Lead Time (days)"
                  type="number"
                  value={editMaterial.lead_time_days || ''}
                  onChange={(e) => setEditMaterial({ ...editMaterial, lead_time_days: parseFloat(e.target.value) || undefined })}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  label="Min Order Qty"
                  type="number"
                  value={editMaterial.minimum_order || ''}
                  onChange={(e) => setEditMaterial({ ...editMaterial, minimum_order: parseFloat(e.target.value) || undefined })}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Specifications"
                  value={editMaterial.specifications || ''}
                  onChange={(e) => setEditMaterial({ ...editMaterial, specifications: e.target.value })}
                  fullWidth
                  multiline
                  rows={2}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Notes"
                  value={editMaterial.notes || ''}
                  onChange={(e) => setEditMaterial({ ...editMaterial, notes: e.target.value })}
                  fullWidth
                  multiline
                  rows={2}
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSaveMaterial}
            disabled={saving || !editMaterial?.product_code || !editMaterial?.description}
          >
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
