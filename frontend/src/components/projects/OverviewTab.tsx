import { useState } from 'react';
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
import { Edit, LocationOn, CalendarToday, Category } from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  project: any;
  onProjectUpdate: () => void;
}

export default function OverviewTab({ project, onProjectUpdate }: Props) {
  const [openEdit, setOpenEdit] = useState(false);
  const [formData, setFormData] = useState({
    name: project.name || '',
    location: project.location || '',
    type: project.type || '',
    description: project.description || '',
  });

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
            <Typography variant="h6" gutterBottom>
              Quick Stats
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {project.document_count || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Documents
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {project.takeoff_count || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Takeoff Items
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {project.estimate_count || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Estimates
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {project.spec_count || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Specifications
                  </Typography>
                </Box>
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
