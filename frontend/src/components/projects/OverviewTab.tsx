import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
} from '@mui/material';
import {
  Edit,
  LocationOn,
  CalendarToday,
  Category,
  Description,
  Build,
  Receipt,
  Calculate,
  Inventory,
  Warning,
} from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  project: any;
  onProjectUpdate: () => void;
}

interface Stats {
  documents: number;
  takeoffs: number;
  specs: number;
  quotes: number;
  estimates: number;
  discrepancies: number;
}

export default function OverviewTab({ project, onProjectUpdate }: Props) {
  const [openEdit, setOpenEdit] = useState(false);
  const [stats, setStats] = useState<Stats>({
    documents: 0,
    takeoffs: 0,
    specs: 0,
    quotes: 0,
    estimates: 0,
    discrepancies: 0,
  });
  const [formData, setFormData] = useState({
    name: project.name || '',
    location: project.location || '',
    type: project.type || '',
    description: project.description || '',
  });

  useEffect(() => {
    loadStats();
  }, [project.id]);

  const loadStats = async () => {
    try {
      // Load all stats in parallel
      const [docsRes, takeoffsRes, specsRes, quotesRes] = await Promise.all([
        api.get(`/projects/${project.id}/documents`).catch(() => ({ data: [] })),
        api.get(`/projects/${project.id}/takeoffs`).catch(() => ({ data: [] })),
        api.get(`/projects/${project.id}/specifications`).catch(() => ({ data: { specifications: [] } })),
        api.get(`/projects/${project.id}/generated-quotes`).catch(() => ({ data: { quotes: [] } })),
      ]);

      setStats({
        documents: docsRes.data?.length || 0,
        takeoffs: takeoffsRes.data?.length || 0,
        specs: specsRes.data?.specifications?.length || specsRes.data?.length || 0,
        quotes: quotesRes.data?.quotes?.length || 0,
        estimates: project.estimate_count || 0,
        discrepancies: project.discrepancy_count || 0,
      });
    } catch (err) {
      console.error('Failed to load stats', err);
    }
  };

  const handleEdit = () => {
    setFormData({
      name: project.name || '',
      location: project.location || '',
      type: project.type || '',
      description: project.description || '',
    });
    setOpenEdit(true);
  };

  const handleSave = async () => {
    try {
      await api.put(`/projects/${project.id}`, formData);
      onProjectUpdate();
      setOpenEdit(false);
    } catch (err) {
      console.error('Failed to update project', err);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Project Overview</Typography>
        <Button startIcon={<Edit />} onClick={handleEdit}>
          Edit Details
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Basic Info Card */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Category color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Project Name
                  </Typography>
                  <Typography variant="body1">{project.name}</Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LocationOn color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Location
                  </Typography>
                  <Typography variant="body1">
                    {project.location || 'Not specified'}
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CalendarToday color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body1">
                    {new Date(project.created_at).toLocaleDateString()}
                  </Typography>
                </Box>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Job Number
                </Typography>
                <Typography variant="body1">{project.job_number}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Type
                </Typography>
                <Typography variant="body1">{project.type || 'Not specified'}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Status
                </Typography>
                <Box sx={{ mt: 0.5 }}>
                  <Chip
                    label={project.status || 'Active'}
                    color={project.status === 'completed' ? 'success' : 'primary'}
                    size="small"
                  />
                </Box>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Description Card */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Description
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              {project.description || 'No description provided'}
            </Typography>
          </Paper>
        </Grid>

        {/* Quick Stats Card */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
              Quick Stats
            </Typography>
            <Grid container spacing={2}>
              {/* Documents */}
              <Grid item xs={6} sm={4} md={2}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    textAlign: 'center',
                    bgcolor: 'primary.50',
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'primary.100',
                  }}
                >
                  <Description sx={{ fontSize: 28, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h4" fontWeight="bold" color="primary.main">
                    {stats.documents}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight="medium">
                    Documents
                  </Typography>
                </Paper>
              </Grid>

              {/* Takeoffs */}
              <Grid item xs={6} sm={4} md={2}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    textAlign: 'center',
                    bgcolor: 'secondary.50',
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'secondary.100',
                  }}
                >
                  <Build sx={{ fontSize: 28, color: 'secondary.main', mb: 1 }} />
                  <Typography variant="h4" fontWeight="bold" color="secondary.main">
                    {stats.takeoffs}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight="medium">
                    Takeoff Items
                  </Typography>
                </Paper>
              </Grid>

              {/* Specifications */}
              <Grid item xs={6} sm={4} md={2}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    textAlign: 'center',
                    bgcolor: 'info.50',
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'info.100',
                  }}
                >
                  <Inventory sx={{ fontSize: 28, color: 'info.main', mb: 1 }} />
                  <Typography variant="h4" fontWeight="bold" color="info.main">
                    {stats.specs}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight="medium">
                    Specifications
                  </Typography>
                </Paper>
              </Grid>

              {/* Quotes */}
              <Grid item xs={6} sm={4} md={2}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    textAlign: 'center',
                    bgcolor: 'success.50',
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'success.100',
                  }}
                >
                  <Receipt sx={{ fontSize: 28, color: 'success.main', mb: 1 }} />
                  <Typography variant="h4" fontWeight="bold" color="success.main">
                    {stats.quotes}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight="medium">
                    Quotes
                  </Typography>
                </Paper>
              </Grid>

              {/* Estimates */}
              <Grid item xs={6} sm={4} md={2}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    textAlign: 'center',
                    bgcolor: 'warning.50',
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'warning.100',
                  }}
                >
                  <Calculate sx={{ fontSize: 28, color: 'warning.main', mb: 1 }} />
                  <Typography variant="h4" fontWeight="bold" color="warning.main">
                    {stats.estimates}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight="medium">
                    Estimates
                  </Typography>
                </Paper>
              </Grid>

              {/* Discrepancies */}
              <Grid item xs={6} sm={4} md={2}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    textAlign: 'center',
                    bgcolor: stats.discrepancies > 0 ? 'error.50' : 'grey.50',
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: stats.discrepancies > 0 ? 'error.100' : 'grey.200',
                  }}
                >
                  <Warning sx={{ fontSize: 28, color: stats.discrepancies > 0 ? 'error.main' : 'grey.400', mb: 1 }} />
                  <Typography variant="h4" fontWeight="bold" color={stats.discrepancies > 0 ? 'error.main' : 'grey.500'}>
                    {stats.discrepancies}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight="medium">
                    Discrepancies
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      {/* Edit Dialog */}
      <Dialog open={openEdit} onClose={() => setOpenEdit(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Project Details</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Project Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Location"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              fullWidth
            />
            <TextField
              label="Type"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              fullWidth
            />
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              multiline
              rows={4}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEdit(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
