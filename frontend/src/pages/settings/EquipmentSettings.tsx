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
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { Add, Edit, Delete, ArrowBack } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface Equipment {
  id: string;
  name: string;
  equipment_type: string;
  model?: string;
  serial_number?: string;
  purchase_price?: number;
  hourly_cost: number;
  is_available: boolean;
  condition: string;
  notes?: string;
}

interface EquipmentFormData {
  name: string;
  equipment_type: string;
  model: string;
  serial_number: string;
  purchase_price: string;
  hourly_cost: string;
  condition: string;
  notes: string;
}

const conditionOptions = [
  { value: 'good', label: 'Good', color: 'success' },
  { value: 'fair', label: 'Fair', color: 'warning' },
  { value: 'poor', label: 'Poor', color: 'error' },
  { value: 'maintenance', label: 'In Maintenance', color: 'info' },
  { value: 'out_of_service', label: 'Out of Service', color: 'default' },
];

const equipmentTypes = [
  'Excavator',
  'Bulldozer',
  'Backhoe',
  'Loader',
  'Grader',
  'Roller',
  'Dump Truck',
  'Crane',
  'Forklift',
  'Compactor',
  'Paver',
  'Trencher',
  'Other',
];

export default function EquipmentSettings() {
  const navigate = useNavigate();
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [formData, setFormData] = useState<EquipmentFormData>({
    name: '',
    equipment_type: '',
    model: '',
    serial_number: '',
    purchase_price: '',
    hourly_cost: '',
    condition: 'good',
    notes: '',
  });
  const [filterType, setFilterType] = useState('');
  const [filterCondition, setFilterCondition] = useState('');

  useEffect(() => {
    fetchEquipment();
  }, []);

  const fetchEquipment = async () => {
    try {
      setLoading(true);
      const response = await api.get('/equipment');
      setEquipment(response.data);
      setError('');
    } catch (err: any) {
      console.error('Failed to fetch equipment', err);
      setError(err.response?.data?.detail || 'Failed to load equipment');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (equipmentItem?: Equipment) => {
    if (equipmentItem) {
      setEditingId(equipmentItem.id);
      setFormData({
        name: equipmentItem.name,
        equipment_type: equipmentItem.equipment_type,
        model: equipmentItem.model || '',
        serial_number: equipmentItem.serial_number || '',
        purchase_price: equipmentItem.purchase_price?.toString() || '',
        hourly_cost: equipmentItem.hourly_cost.toString(),
        condition: equipmentItem.condition,
        notes: equipmentItem.notes || '',
      });
    } else {
      setEditingId(null);
      setFormData({
        name: '',
        equipment_type: '',
        model: '',
        serial_number: '',
        purchase_price: '',
        hourly_cost: '',
        condition: 'good',
        notes: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingId(null);
  };

  const handleChange = (field: keyof EquipmentFormData, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async () => {
    try {
      const payload = {
        name: formData.name,
        equipment_type: formData.equipment_type,
        model: formData.model || null,
        serial_number: formData.serial_number || null,
        purchase_price: formData.purchase_price ? parseFloat(formData.purchase_price) : null,
        hourly_cost: parseFloat(formData.hourly_cost),
        is_available: formData.condition === 'good' || formData.condition === 'fair',
        condition: formData.condition,
        notes: formData.notes || null,
      };

      if (editingId) {
        await api.put(`/equipment/${editingId}`, payload);
      } else {
        await api.post('/equipment', payload);
      }

      await fetchEquipment();
      handleCloseDialog();
      setError('');
    } catch (err: any) {
      console.error('Failed to save equipment', err);
      setError(err.response?.data?.detail || 'Failed to save equipment');
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirmId) return;

    try {
      await api.delete(`/equipment/${deleteConfirmId}`);
      await fetchEquipment();
      setDeleteConfirmId(null);
      setError('');
    } catch (err: any) {
      console.error('Failed to delete equipment', err);
      setError(err.response?.data?.detail || 'Failed to delete equipment');
      setDeleteConfirmId(null);
    }
  };

  const handleToggleAvailability = async (id: string, currentAvailability: boolean) => {
    try {
      await api.patch(`/equipment/${id}/availability`, {
        is_available: !currentAvailability,
      });
      await fetchEquipment();
      setError('');
    } catch (err: any) {
      console.error('Failed to update availability', err);
      setError(err.response?.data?.detail || 'Failed to update availability');
    }
  };

  const getConditionChip = (condition: string) => {
    const option = conditionOptions.find((opt) => opt.value === condition);
    return (
      <Chip
        label={option?.label || condition}
        color={option?.color as any}
        size="small"
      />
    );
  };

  const getAvailabilityChip = (isAvailable: boolean) => {
    return (
      <Chip
        label={isAvailable ? 'Available' : 'In Use'}
        color={isAvailable ? 'success' : 'default'}
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
      field: 'equipment_type',
      headerName: 'Type',
      flex: 1,
      minWidth: 120,
    },
    {
      field: 'model',
      headerName: 'Model',
      flex: 1,
      minWidth: 120,
    },
    {
      field: 'hourly_cost',
      headerName: 'Hourly Cost',
      width: 120,
      renderCell: (params: GridRenderCellParams) => `$${parseFloat(params.value || 0).toFixed(2)}`,
    },
    {
      field: 'condition',
      headerName: 'Condition',
      width: 150,
      renderCell: (params: GridRenderCellParams) => getConditionChip(params.value),
    },
    {
      field: 'is_available',
      headerName: 'Status',
      width: 120,
      renderCell: (params: GridRenderCellParams) => getAvailabilityChip(params.value),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 150,
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
            onClick={() =>
              handleToggleAvailability(params.row.id, params.row.is_available)
            }
            color="info"
          >
            {params.row.is_available ? '🔒' : '🔓'}
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

  const filteredEquipment = equipment.filter((item) => {
    if (filterType && item.equipment_type !== filterType) return false;
    if (filterCondition && item.condition !== filterCondition) return false;
    return true;
  });

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <IconButton onClick={() => navigate('/dashboard')} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h4">Equipment Management</Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Manage your company's internal equipment inventory
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => handleOpenDialog()}
          >
            Add Equipment
          </Button>
          <TextField
            select
            label="Filter by Type"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            sx={{ minWidth: 200 }}
            size="small"
          >
            <MenuItem value="">All Types</MenuItem>
            {equipmentTypes.map((type) => (
              <MenuItem key={type} value={type}>
                {type}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label="Filter by Condition"
            value={filterCondition}
            onChange={(e) => setFilterCondition(e.target.value)}
            sx={{ minWidth: 200 }}
            size="small"
          >
            <MenuItem value="">All Conditions</MenuItem>
            {conditionOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <DataGrid
            rows={filteredEquipment}
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
        <DialogTitle>{editingId ? 'Edit Equipment' : 'Add Equipment'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Equipment Name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              required
              fullWidth
            />
            <TextField
              select
              label="Equipment Type"
              value={formData.equipment_type}
              onChange={(e) => handleChange('equipment_type', e.target.value)}
              required
              fullWidth
            >
              {equipmentTypes.map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Model"
              value={formData.model}
              onChange={(e) => handleChange('model', e.target.value)}
              fullWidth
            />
            <TextField
              label="Serial Number"
              value={formData.serial_number}
              onChange={(e) => handleChange('serial_number', e.target.value)}
              fullWidth
            />
            <TextField
              label="Purchase Price"
              type="number"
              value={formData.purchase_price}
              onChange={(e) => handleChange('purchase_price', e.target.value)}
              fullWidth
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              label="Hourly Operating Cost"
              type="number"
              value={formData.hourly_cost}
              onChange={(e) => handleChange('hourly_cost', e.target.value)}
              required
              fullWidth
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              select
              label="Condition"
              value={formData.condition}
              onChange={(e) => handleChange('condition', e.target.value)}
              required
              fullWidth
            >
              {conditionOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
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
            disabled={!formData.name || !formData.equipment_type || !formData.hourly_cost}
          >
            {editingId ? 'Update' : 'Create'}
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
            Are you sure you want to delete this equipment? This action cannot be undone.
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
