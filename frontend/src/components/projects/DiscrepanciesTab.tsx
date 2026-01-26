import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Collapse,
  MenuItem,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Search as SearchIcon,
  ExpandMore,
  ExpandLess,
  CheckCircle,
  VisibilityOff,
  Info,
} from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  projectId: string;
  onCountUpdate: (count: number) => void;
}

interface Discrepancy {
  id: string;
  discrepancy_type: string;
  severity: string;
  bid_item_description: string;
  bid_quantity?: number;
  plan_quantity?: number;
  difference_percentage?: number;
  notes?: string;
  status: string;
  resolution_notes?: string;
}

const severityConfig = {
  critical: { color: 'error' as const, label: 'Critical', emoji: '🔴' },
  high: { color: 'warning' as const, label: 'High', emoji: '🟠' },
  medium: { color: 'info' as const, label: 'Medium', emoji: '🟡' },
  low: { color: 'success' as const, label: 'Low', emoji: '🟢' },
};

const typeLabels: any = {
  quantity_mismatch: 'Quantity Mismatch',
  missing_item: 'Missing Item',
  extra_item: 'Extra Item',
};

export default function DiscrepanciesTab({ projectId, onCountUpdate }: Props) {
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[]>([]);
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [resolveDialog, setResolveDialog] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  useEffect(() => {
    loadDiscrepancies();
  }, [projectId]);

  const loadDiscrepancies = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/discrepancies`);
      const activeDiscrepancies = response.data.filter(
        (d: Discrepancy) => d.status === 'pending'
      );
      setDiscrepancies(response.data);
      onCountUpdate(activeDiscrepancies.length);
    } catch (err) {
      console.error('Failed to load discrepancies', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDetectDiscrepancies = async () => {
    try {
      setDetecting(true);
      setError('');
      const response = await api.post(`/projects/${projectId}/discrepancies/detect`);
      setMessage(
        `Detection complete! Found ${response.data.discrepancies_found || 0} discrepancies`
      );
      setTimeout(() => setMessage(''), 3000);
      await loadDiscrepancies();
    } catch (err: any) {
      console.error('Failed to detect discrepancies', err);
      setError(err.response?.data?.detail || 'Failed to detect discrepancies');
    } finally {
      setDetecting(false);
    }
  };

  const handleResolve = async () => {
    if (!resolveDialog) return;

    try {
      await api.patch(`/discrepancies/${resolveDialog}/status`, {
        status: 'resolved',
        resolution_notes: resolutionNotes,
      });
      setMessage('Discrepancy marked as resolved');
      setTimeout(() => setMessage(''), 2000);
      await loadDiscrepancies();
      setResolveDialog(null);
      setResolutionNotes('');
    } catch (err: any) {
      console.error('Failed to resolve discrepancy', err);
      setError(err.response?.data?.detail || 'Failed to resolve discrepancy');
    }
  };

  const handleIgnore = async (id: string) => {
    try {
      await api.patch(`/discrepancies/${id}/status`, {
        status: 'ignored',
      });
      setMessage('Discrepancy ignored');
      setTimeout(() => setMessage(''), 2000);
      await loadDiscrepancies();
    } catch (err: any) {
      console.error('Failed to ignore discrepancy', err);
      setError(err.response?.data?.detail || 'Failed to ignore discrepancy');
    }
  };

  const filteredDiscrepancies = discrepancies.filter((d) => {
    if (filterSeverity !== 'all' && d.severity !== filterSeverity) return false;
    if (filterType !== 'all' && d.discrepancy_type !== filterType) return false;
    return true;
  });

  const getSeverityChip = (severity: string) => {
    const config = severityConfig[severity as keyof typeof severityConfig] || {
      color: 'default' as const,
      label: severity,
      emoji: '⚪',
    };
    return (
      <Chip
        label={`${config.emoji} ${config.label}`}
        color={config.color}
        size="small"
      />
    );
  };

  const getStatusChip = (status: string) => {
    const colorMap: any = {
      pending: 'warning',
      resolved: 'success',
      ignored: 'default',
    };
    return <Chip label={status} color={colorMap[status] || 'default'} size="small" />;
  };

  const severityCounts = {
    critical: discrepancies.filter((d) => d.severity === 'critical' && d.status === 'pending').length,
    high: discrepancies.filter((d) => d.severity === 'high' && d.status === 'pending').length,
    medium: discrepancies.filter((d) => d.severity === 'medium' && d.status === 'pending').length,
    low: discrepancies.filter((d) => d.severity === 'low' && d.status === 'pending').length,
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Discrepancies</Typography>
        <Button
          variant="contained"
          startIcon={detecting ? <CircularProgress size={20} /> : <SearchIcon />}
          onClick={handleDetectDiscrepancies}
          disabled={detecting}
        >
          {detecting ? 'Detecting...' : 'Run Detection'}
        </Button>
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

      {/* Summary Card */}
      {discrepancies.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Summary
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            {severityCounts.critical > 0 && (
              <Chip
                label={`${severityCounts.critical} Critical`}
                color="error"
                size="small"
              />
            )}
            {severityCounts.high > 0 && (
              <Chip
                label={`${severityCounts.high} High`}
                color="warning"
                size="small"
              />
            )}
            {severityCounts.medium > 0 && (
              <Chip
                label={`${severityCounts.medium} Medium`}
                color="info"
                size="small"
              />
            )}
            {severityCounts.low > 0 && (
              <Chip
                label={`${severityCounts.low} Low`}
                color="success"
                size="small"
              />
            )}
          </Box>
        </Paper>
      )}

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          select
          label="Filter by Severity"
          value={filterSeverity}
          onChange={(e) => setFilterSeverity(e.target.value)}
          size="small"
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="all">All Severities</MenuItem>
          <MenuItem value="critical">Critical</MenuItem>
          <MenuItem value="high">High</MenuItem>
          <MenuItem value="medium">Medium</MenuItem>
          <MenuItem value="low">Low</MenuItem>
        </TextField>
        <TextField
          select
          label="Filter by Type"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          size="small"
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="all">All Types</MenuItem>
          <MenuItem value="quantity_mismatch">Quantity Mismatch</MenuItem>
          <MenuItem value="missing_item">Missing Item</MenuItem>
          <MenuItem value="extra_item">Extra Item</MenuItem>
        </TextField>
      </Box>

      {/* Discrepancies List */}
      <Paper>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : filteredDiscrepancies.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Info sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {discrepancies.length === 0
                ? 'No discrepancies detected yet'
                : 'No discrepancies match your filters'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {discrepancies.length === 0
                ? 'Run detection to compare bid items with plan quantities'
                : 'Try adjusting your filters'}
            </Typography>
          </Box>
        ) : (
          <List>
            {filteredDiscrepancies.map((disc) => (
              <Box key={disc.id}>
                <ListItem>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {getSeverityChip(disc.severity)}
                      <Chip
                        label={typeLabels[disc.discrepancy_type] || disc.discrepancy_type}
                        size="small"
                        variant="outlined"
                      />
                      {getStatusChip(disc.status)}
                    </Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {disc.bid_item_description}
                    </Typography>
                    {disc.discrepancy_type === 'quantity_mismatch' && (
                      <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Bid: {disc.bid_quantity}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Plan: {disc.plan_quantity}
                        </Typography>
                        <Typography variant="body2" color="error.main" fontWeight="bold">
                          Difference: {disc.difference_percentage?.toFixed(1)}%
                        </Typography>
                      </Box>
                    )}
                    {disc.notes && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {disc.notes}
                      </Typography>
                    )}
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {disc.status === 'pending' && (
                      <>
                        <Button
                          size="small"
                          variant="outlined"
                          color="success"
                          startIcon={<CheckCircle />}
                          onClick={() => setResolveDialog(disc.id)}
                        >
                          Resolve
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<VisibilityOff />}
                          onClick={() => handleIgnore(disc.id)}
                        >
                          Ignore
                        </Button>
                      </>
                    )}
                    <IconButton
                      size="small"
                      onClick={() => setExpandedId(expandedId === disc.id ? null : disc.id)}
                    >
                      {expandedId === disc.id ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </Box>
                </ListItem>
                <Collapse in={expandedId === disc.id}>
                  <Box sx={{ px: 2, pb: 2 }}>
                    <Typography variant="body2" paragraph>
                      <strong>Recommendation:</strong> {getRecommendation(disc)}
                    </Typography>
                    {disc.resolution_notes && (
                      <Alert severity="info" sx={{ mt: 1 }}>
                        <strong>Resolution Notes:</strong> {disc.resolution_notes}
                      </Alert>
                    )}
                  </Box>
                </Collapse>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }} />
              </Box>
            ))}
          </List>
        )}
      </Paper>

      {/* Resolve Dialog */}
      <Dialog open={!!resolveDialog} onClose={() => setResolveDialog(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Resolve Discrepancy</DialogTitle>
        <DialogContent>
          <TextField
            label="Resolution Notes"
            placeholder="Describe how this was resolved..."
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            multiline
            rows={4}
            fullWidth
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResolveDialog(null)}>Cancel</Button>
          <Button onClick={handleResolve} variant="contained" color="success">
            Mark as Resolved
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

function getRecommendation(disc: Discrepancy): string {
  switch (disc.discrepancy_type) {
    case 'quantity_mismatch':
      if (disc.severity === 'critical') {
        return 'Critical difference detected. Verify plans and update bid quantities immediately.';
      }
      return 'Review plans and confirm correct quantity before proceeding.';
    case 'missing_item':
      return 'This item appears in the bid but not in the plans. Verify if it should be removed or if plans are incomplete.';
    case 'extra_item':
      return 'This item appears in the plans but not in the bid. Consider adding to bid or verify if it should be excluded.';
    default:
      return 'Review and resolve this discrepancy.';
  }
}
