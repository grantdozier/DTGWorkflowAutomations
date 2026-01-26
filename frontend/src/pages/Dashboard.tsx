import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Chip,
  CircularProgress,
  IconButton,
} from '@mui/material';
import { Add, FolderOpen, LocationOn, Work, Delete } from '@mui/icons-material';
import { getProjects, createProject, deleteProject } from '../services/api';
import Layout from '../components/Layout';

export default function Dashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [newProject, setNewProject] = useState({
    name: '',
    job_number: '',
    location: '',
    type: 'state',
  });
  const [error, setError] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<any>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await getProjects();
      setProjects(response.data.projects);
    } catch (err) {
      console.error('Failed to load projects', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async () => {
    setError('');
    try {
      await createProject(newProject);
      setOpenDialog(false);
      setNewProject({ name: '', job_number: '', location: '', type: 'state' });
      loadProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create project');
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, project: any) => {
    e.stopPropagation();
    setProjectToDelete(project);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!projectToDelete) return;
    setDeleting(true);
    try {
      await deleteProject(projectToDelete.id);
      setDeleteDialogOpen(false);
      setProjectToDelete(null);
      loadProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete project');
    } finally {
      setDeleting(false);
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'state': return { bg: '#dbeafe', color: '#1e40af' };
      case 'federal': return { bg: '#fef3c7', color: '#92400e' };
      case 'private': return { bg: '#d1fae5', color: '#065f46' };
      default: return { bg: '#f3f4f6', color: '#374151' };
    }
  };

  return (
    <Layout>
      <Box sx={{ bgcolor: 'white', borderBottom: '1px solid', borderColor: 'grey.200' }}>
        <Container maxWidth="lg">
          <Box sx={{ py: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, color: 'grey.900' }}>
                Projects
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Manage your construction projects and estimates
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setOpenDialog(true)}
              sx={{
                px: 3,
                py: 1.5,
                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                },
              }}
            >
              New Project
            </Button>
          </Box>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : projects.length === 0 ? (
          <Box 
            sx={{ 
              textAlign: 'center', 
              py: 8,
              px: 4,
              bgcolor: 'white',
              borderRadius: 3,
              border: '2px dashed',
              borderColor: 'grey.300',
            }}
          >
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                bgcolor: 'primary.50',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 2,
              }}
            >
              <FolderOpen sx={{ fontSize: 32, color: 'primary.main' }} />
            </Box>
            <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
              No projects yet
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 3 }}>
              Create your first project to get started with estimates
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setOpenDialog(true)}
            >
              Create Project
            </Button>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {projects.map((project) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    border: '1px solid',
                    borderColor: 'grey.200',
                    '&:hover': {
                      borderColor: 'primary.main',
                      transform: 'translateY(-2px)',
                    },
                    position: 'relative',
                  }}
                  onClick={() => navigate(`/project/${project.id}`)}
                >
                  <IconButton
                    size="small"
                    onClick={(e) => handleDeleteClick(e, project)}
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      opacity: 0.5,
                      '&:hover': {
                        opacity: 1,
                        color: 'error.main',
                        bgcolor: 'error.50',
                      },
                    }}
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2, pr: 3 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, flex: 1 }}>
                        {project.name}
                      </Typography>
                      <Chip
                        label={project.type || 'N/A'}
                        size="small"
                        sx={{
                          bgcolor: getTypeColor(project.type).bg,
                          color: getTypeColor(project.type).color,
                          fontWeight: 500,
                          textTransform: 'capitalize',
                        }}
                      />
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Work sx={{ fontSize: 16, color: 'grey.400' }} />
                        <Typography variant="body2" color="text.secondary">
                          {project.job_number}
                        </Typography>
                      </Box>
                      {project.location && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LocationOn sx={{ fontSize: 16, color: 'grey.400' }} />
                          <Typography variant="body2" color="text.secondary">
                            {project.location}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>

      {/* Create Project Dialog */}
      <Dialog 
        open={openDialog} 
        onClose={() => setOpenDialog(false)} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: { borderRadius: 3 }
        }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            Create New Project
          </Typography>
        </DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>}
          <TextField
            fullWidth
            label="Project Name"
            value={newProject.name}
            onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
            margin="normal"
            required
            InputProps={{ sx: { bgcolor: 'grey.50' } }}
          />
          <TextField
            fullWidth
            label="Job Number"
            value={newProject.job_number}
            onChange={(e) => setNewProject({ ...newProject, job_number: e.target.value })}
            margin="normal"
            required
            InputProps={{ sx: { bgcolor: 'grey.50' } }}
          />
          <TextField
            fullWidth
            label="Location"
            value={newProject.location}
            onChange={(e) => setNewProject({ ...newProject, location: e.target.value })}
            margin="normal"
            InputProps={{ sx: { bgcolor: 'grey.50' } }}
          />
          <TextField
            fullWidth
            select
            label="Type"
            value={newProject.type}
            onChange={(e) => setNewProject({ ...newProject, type: e.target.value })}
            margin="normal"
            SelectProps={{ native: true }}
            InputProps={{ sx: { bgcolor: 'grey.50' } }}
          >
            <option value="state">State</option>
            <option value="private">Private</option>
            <option value="federal">Federal</option>
          </TextField>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 1 }}>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateProject} 
            variant="contained"
            sx={{
              px: 3,
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            }}
          >
            Create Project
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="xs"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Delete Project?
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            Are you sure you want to delete <strong>{projectToDelete?.name}</strong>? This action cannot be undone and will remove all associated documents, estimates, and data.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 1 }}>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete Project'}
          </Button>
        </DialogActions>
      </Dialog>
    </Layout>
  );
}
