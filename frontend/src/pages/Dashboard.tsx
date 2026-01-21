import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  AppBar,
  Toolbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from '@mui/material';
import { Add, Logout } from '@mui/icons-material';
import { getProjects, createProject } from '../services/api';

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

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
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

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            DTG Workflow Automations
          </Typography>
          <Button color="inherit" startIcon={<Logout />} onClick={handleLogout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h4">Projects</Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setOpenDialog(true)}
          >
            New Project
          </Button>
        </Box>

        {loading ? (
          <Typography>Loading projects...</Typography>
        ) : projects.length === 0 ? (
          <Typography color="text.secondary">
            No projects yet. Create your first project to get started.
          </Typography>
        ) : (
          <Grid container spacing={3}>
            {projects.map((project) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {project.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Job #: {project.job_number}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Location: {project.location || 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Type: {project.type || 'N/A'}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      onClick={() => navigate(`/project/${project.id}`)}
                    >
                      Open
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>

      {/* Create Project Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            fullWidth
            label="Project Name"
            value={newProject.name}
            onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Job Number"
            value={newProject.job_number}
            onChange={(e) => setNewProject({ ...newProject, job_number: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Location"
            value={newProject.location}
            onChange={(e) => setNewProject({ ...newProject, location: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            select
            label="Type"
            value={newProject.type}
            onChange={(e) => setNewProject({ ...newProject, type: e.target.value })}
            margin="normal"
            SelectProps={{ native: true }}
          >
            <option value="state">State</option>
            <option value="private">Private</option>
            <option value="federal">Federal</option>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateProject} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
