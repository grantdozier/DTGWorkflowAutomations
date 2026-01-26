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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Calculate,
  ExpandMore,
  Download,
  TrendingUp,
  CheckCircle,
} from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  projectId: string;
}

interface Estimate {
  id: string;
  created_at: string;
  total_cost: number;
  materials_cost: number;
  labor_cost: number;
  equipment_cost: number;
  overhead: number;
  profit: number;
  bond?: number;
  contingency?: number;
  confidence_score?: number;
  breakdown?: any;
}

export default function EstimatesTab({ projectId }: Props) {
  const [estimates, setEstimates] = useState<Estimate[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [expandedEstimate, setExpandedEstimate] = useState<string | null>(null);

  useEffect(() => {
    loadEstimates();
  }, [projectId]);

  const loadEstimates = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/estimates`);
      setEstimates(response.data.estimates || []);
    } catch (err) {
      console.error('Failed to load estimates', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateEstimate = async () => {
    try {
      setGenerating(true);
      setError('');
      const response = await api.post(`/projects/${projectId}/estimate`);
      setMessage(`Estimate generated! Total: $${response.data.breakdown.total.toLocaleString()}`);
      setTimeout(() => setMessage(''), 3000);
      await loadEstimates();
    } catch (err: any) {
      console.error('Failed to generate estimate', err);
      setError(err.response?.data?.detail || 'Failed to generate estimate');
    } finally {
      setGenerating(false);
    }
  };

  const handleExportPDF = async (estimateId: string) => {
    try {
      const response = await api.get(
        `/projects/${projectId}/estimates/${estimateId}/export`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `estimate-${projectId}-${estimateId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to export estimate', err);
      setError('Failed to export estimate');
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Cost Estimates</Typography>
        <Button
          variant="contained"
          color="success"
          startIcon={generating ? <CircularProgress size={20} /> : <Calculate />}
          onClick={handleGenerateEstimate}
          disabled={generating}
        >
          {generating ? 'Generating...' : 'Generate New Estimate'}
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

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : estimates.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Calculate sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No estimates generated yet
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Upload documents and extract takeoffs, then generate an estimate
          </Typography>
          <Button
            variant="contained"
            color="success"
            startIcon={<Calculate />}
            onClick={handleGenerateEstimate}
            disabled={generating}
          >
            Generate First Estimate
          </Button>
        </Paper>
      ) : (
        <Box>
          {estimates.map((estimate, index) => (
            <Card key={estimate.id} sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Box>
                    <Typography variant="h6">
                      Estimate #{estimates.length - index}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Generated {new Date(estimate.created_at).toLocaleString()}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    {estimate.confidence_score && (
                      <Chip
                        icon={<CheckCircle />}
                        label={`Confidence: ${estimate.confidence_score}%`}
                        color="success"
                        size="small"
                      />
                    )}
                    <Button
                      size="small"
                      startIcon={<Download />}
                      onClick={() => handleExportPDF(estimate.id)}
                    >
                      Export PDF
                    </Button>
                  </Box>
                </Box>

                {/* Total Cost Highlight */}
                <Paper
                  sx={{
                    p: 3,
                    mb: 2,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                  }}
                >
                  <Typography variant="h3" align="center" fontWeight="bold">
                    {formatCurrency(estimate.total_cost)}
                  </Typography>
                  <Typography variant="subtitle1" align="center">
                    Total Estimated Cost
                  </Typography>
                </Paper>

                {/* Cost Breakdown Grid */}
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6} sm={4} md={2}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Materials
                      </Typography>
                      <Typography variant="h6" color="primary">
                        {formatCurrency(estimate.materials_cost)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} sm={4} md={2}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Labor
                      </Typography>
                      <Typography variant="h6" color="primary">
                        {formatCurrency(estimate.labor_cost)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} sm={4} md={2}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Equipment
                      </Typography>
                      <Typography variant="h6" color="primary">
                        {formatCurrency(estimate.equipment_cost)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} sm={4} md={2}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Overhead
                      </Typography>
                      <Typography variant="h6" color="primary">
                        {formatCurrency(estimate.overhead)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} sm={4} md={2}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Profit
                      </Typography>
                      <Typography variant="h6" color="primary">
                        {formatCurrency(estimate.profit)}
                      </Typography>
                    </Paper>
                  </Grid>
                  {estimate.bond && (
                    <Grid item xs={6} sm={4} md={2}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">
                          Bond
                        </Typography>
                        <Typography variant="h6" color="primary">
                          {formatCurrency(estimate.bond)}
                        </Typography>
                      </Paper>
                    </Grid>
                  )}
                </Grid>

                {/* Detailed Breakdown Accordion */}
                {estimate.breakdown && (
                  <Accordion
                    expanded={expandedEstimate === estimate.id}
                    onChange={() =>
                      setExpandedEstimate(expandedEstimate === estimate.id ? null : estimate.id)
                    }
                  >
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography>Detailed Breakdown</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Item</TableCell>
                              <TableCell align="right">Quantity</TableCell>
                              <TableCell align="right">Unit Cost</TableCell>
                              <TableCell align="right">Total</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {estimate.breakdown.items?.map((item: any, idx: number) => (
                              <TableRow key={idx}>
                                <TableCell>{item.description}</TableCell>
                                <TableCell align="right">
                                  {item.quantity} {item.unit}
                                </TableCell>
                                <TableCell align="right">{formatCurrency(item.unit_cost)}</TableCell>
                                <TableCell align="right">{formatCurrency(item.total)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </AccordionDetails>
                  </Accordion>
                )}
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
}
