import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  IconButton,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { Add, Delete, Download, AutoFixHigh, AttachMoney, DeleteSweep } from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  projectId: string;
  onCountUpdate: (count: number) => void;
}

interface TakeoffItem {
  id: string;
  label: string;
  description: string;
  quantity: number;
  unit: string;
  source_page?: number;
  category?: string;
  quote_status?: string;
  matched_material_id?: string;
  unit_price?: number;
  total_price?: number;
  matched_material?: string;
  product_code?: string;
}

export default function TakeoffsTab({ projectId, onCountUpdate }: Props) {
  const [takeoffs, setTakeoffs] = useState<TakeoffItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [matching, setMatching] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [subtotal, setSubtotal] = useState(0);

  useEffect(() => {
    loadTakeoffs();
  }, [projectId]);

  const loadTakeoffs = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/takeoffs`);
      setTakeoffs(response.data);
      onCountUpdate(response.data.length);
      // Calculate subtotal from items with prices
      const total = response.data.reduce((sum: number, item: TakeoffItem) => 
        sum + (item.total_price || 0), 0);
      setSubtotal(total);
    } catch (err) {
      console.error('Failed to load takeoffs', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMatchToCatalog = async () => {
    try {
      setMatching(true);
      setMessage('Matching items to material catalog...');
      const response = await api.post(`/matching/match/project/${projectId}/apply`);
      setMessage(`Matched ${response.data.matched} of ${response.data.total_items} items. Subtotal: $${response.data.subtotal.toFixed(2)}`);
      setSubtotal(response.data.subtotal);
      await loadTakeoffs();
    } catch (err: any) {
      console.error('Failed to match items', err);
      setError(err.response?.data?.detail || 'Failed to match items to catalog');
    } finally {
      setMatching(false);
    }
  };

  const handleCellEdit = async (params: any) => {
    try {
      const { id, field, value } = params;
      await api.patch(`/projects/${projectId}/takeoffs/${id}`, {
        [field]: value,
      });
      setMessage('Takeoff updated successfully');
      setTimeout(() => setMessage(''), 2000);
      await loadTakeoffs();
    } catch (err: any) {
      console.error('Failed to update takeoff', err);
      setError(err.response?.data?.detail || 'Failed to update takeoff');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/projects/${projectId}/takeoffs/${id}`);
      setMessage('Takeoff deleted successfully');
      setTimeout(() => setMessage(''), 2000);
      await loadTakeoffs();
    } catch (err: any) {
      console.error('Failed to delete takeoff', err);
      setError(err.response?.data?.detail || 'Failed to delete takeoff');
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm(`Are you sure you want to delete all ${takeoffs.length} takeoff items? This cannot be undone.`)) {
      return;
    }
    try {
      await api.delete(`/projects/${projectId}/takeoffs`);
      setMessage('All takeoff items deleted');
      setTimeout(() => setMessage(''), 2000);
      await loadTakeoffs();
    } catch (err: any) {
      console.error('Failed to delete all takeoffs', err);
      setError(err.response?.data?.detail || 'Failed to delete all takeoffs');
    }
  };

  const handleAddRow = async () => {
    try {
      await api.post(`/projects/${projectId}/takeoffs`, {
        label: 'New Item',
        description: '',
        quantity: 0,
        unit: 'EA',
      });
      setMessage('Takeoff item added');
      setTimeout(() => setMessage(''), 2000);
      await loadTakeoffs();
    } catch (err: any) {
      console.error('Failed to add takeoff', err);
      setError(err.response?.data?.detail || 'Failed to add takeoff');
    }
  };

  const handleExport = () => {
    const csv = [
      ['Item', 'Description', 'Quantity', 'Unit', 'Category', 'Source Page'].join(','),
      ...takeoffs.map((t) =>
        [
          t.label,
          t.description,
          t.quantity,
          t.unit,
          t.category || '',
          t.source_page || '',
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `takeoffs-${projectId}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  
  const columns: GridColDef[] = [
    {
      field: 'label',
      headerName: 'Item',
      flex: 1,
      minWidth: 150,
      editable: true,
    },
    {
      field: 'description',
      headerName: 'Description',
      flex: 2,
      minWidth: 200,
      editable: true,
    },
    {
      field: 'quantity',
      headerName: 'Quantity',
      width: 120,
      editable: true,
      type: 'number',
    },
    {
      field: 'unit',
      headerName: 'Unit',
      width: 100,
      editable: true,
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 120,
      editable: true,
    },
    {
      field: 'unit_price',
      headerName: 'Unit Price',
      width: 100,
      type: 'number',
      valueFormatter: (value: number | null) => value ? `$${value.toFixed(2)}` : '-',
    },
    {
      field: 'total_price',
      headerName: 'Total',
      width: 110,
      type: 'number',
      valueFormatter: (value: number | null) => value ? `$${value.toFixed(2)}` : '-',
    },
    {
      field: 'product_code',
      headerName: 'SKU',
      width: 100,
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
            onClick={() => handleDelete(params.row.id)}
            color="error"
            title="Delete"
          >
            <Delete fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5">Takeoff Items</Typography>
          {subtotal > 0 && (
            <Typography variant="h6" color="success.main" sx={{ mt: 0.5 }}>
              <AttachMoney sx={{ fontSize: 20, verticalAlign: 'middle' }} />
              Estimated Total: ${subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </Typography>
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteSweep />}
            onClick={handleDeleteAll}
            disabled={takeoffs.length === 0}
          >
            Delete All
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<AutoFixHigh />}
            onClick={handleMatchToCatalog}
            disabled={takeoffs.length === 0 || matching}
          >
            {matching ? 'Matching...' : 'Match to Catalog'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleExport}
            disabled={takeoffs.length === 0}
          >
            Export CSV
          </Button>
          <Button variant="contained" startIcon={<Add />} onClick={handleAddRow}>
            Add Item
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
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <DataGrid
            rows={takeoffs}
            columns={columns}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 25 },
              },
            }}
            pageSizeOptions={[10, 25, 50, 100]}
            disableRowSelectionOnClick
            autoHeight
            onCellEditStop={handleCellEdit}
            sx={{ border: 'none' }}
          />
        )}
      </Paper>

      {!loading && takeoffs.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No takeoff items yet
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upload and parse a document to extract takeoff items automatically
          </Typography>
        </Box>
      )}
    </Box>
  );
}
