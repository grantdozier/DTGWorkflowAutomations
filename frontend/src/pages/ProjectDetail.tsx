import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  AppBar,
  Toolbar,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  CircularProgress,
  Card,
  CardContent,
} from '@mui/material';
import { ArrowBack, Upload, AutoAwesome, Calculate } from '@mui/icons-material';
import {
  getProject,
  getDocuments,
  uploadDocument,
  parseDocument,
  generateEstimate,
  getEstimates,
} from '../services/api';

export default function ProjectDetail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [estimates, setEstimates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadProject();
    loadDocuments();
    loadEstimates();
  }, [projectId]);

  const loadProject = async () => {
    try {
      const response = await getProject(projectId!);
      setProject(response.data);
    } catch (err) {
      console.error('Failed to load project', err);
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await getDocuments(projectId!);
      setDocuments(response.data);
    } catch (err) {
      console.error('Failed to load documents', err);
    }
  };

  const loadEstimates = async () => {
    try {
      const response = await getEstimates(projectId!);
      setEstimates(response.data.estimates);
    } catch (err) {
      console.error('Failed to load estimates', err);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError('');
    setMessage('');

    try {
      await uploadDocument(projectId!, file, 'plan');
      setMessage('✅ Document uploaded successfully!');
      loadDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setLoading(false);
    }
  };

  const handleParseDocument = async (documentId: string) => {
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await parseDocument(projectId!, documentId);
      setMessage(`✅ Parsed! Extracted ${response.data.items_saved} items`);
      setTimeout(() => setMessage(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to parse document');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateEstimate = async () => {
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await generateEstimate(projectId!);
      const total = response.data.breakdown.total;
      setMessage(`✅ Estimate generated! Total: $${total.toLocaleString()}`);
      loadEstimates();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate estimate');
    } finally {
      setLoading(false);
    }
  };

  if (!project) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Button color="inherit" startIcon={<ArrowBack />} onClick={() => navigate('/dashboard')}>
            Back
          </Button>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, ml: 2 }}>
            {project.name}
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4 }}>
        {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {/* Project Info */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Project Details
          </Typography>
          <Typography variant="body1">Job Number: {project.job_number}</Typography>
          <Typography variant="body1">Location: {project.location || 'N/A'}</Typography>
          <Typography variant="body1">Type: {project.type || 'N/A'}</Typography>
        </Paper>

        {/* Upload Section */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            1. Upload Plan Document
          </Typography>
          <Button
            variant="contained"
            component="label"
            startIcon={<Upload />}
            disabled={loading}
          >
            Upload PDF Plan
            <input
              type="file"
              hidden
              accept=".pdf"
              onChange={handleFileUpload}
            />
          </Button>

          {documents.length > 0 && (
            <List sx={{ mt: 2 }}>
              {documents.map((doc) => (
                <div key={doc.id}>
                  <ListItem>
                    <ListItemText
                      primary={`Document uploaded at ${new Date(doc.uploaded_at).toLocaleString()}`}
                      secondary={`Type: ${doc.doc_type}`}
                    />
                    <Button
                      variant="outlined"
                      startIcon={<AutoAwesome />}
                      onClick={() => handleParseDocument(doc.id)}
                      disabled={loading}
                      size="small"
                    >
                      Parse with AI
                    </Button>
                  </ListItem>
                  <Divider />
                </div>
              ))}
            </List>
          )}
        </Paper>

        {/* Generate Estimate Section */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            2. Generate Cost Estimate
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            After parsing documents, generate a complete cost estimate
          </Typography>
          <Button
            variant="contained"
            color="success"
            startIcon={<Calculate />}
            onClick={handleGenerateEstimate}
            disabled={loading || documents.length === 0}
          >
            Generate Estimate
          </Button>
        </Paper>

        {/* Estimates List */}
        {estimates.length > 0 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Estimates
            </Typography>
            <List>
              {estimates.map((est) => (
                <Card key={est.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1">
                      Estimate from {new Date(est.created_at).toLocaleDateString()}
                    </Typography>
                    <Typography variant="h5" color="primary" sx={{ mt: 1 }}>
                      Total: ${est.total_cost.toLocaleString()}
                    </Typography>
                    <Box sx={{ mt: 2, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                      <Typography variant="body2">Materials: ${est.materials_cost.toLocaleString()}</Typography>
                      <Typography variant="body2">Labor: ${est.labor_cost.toLocaleString()}</Typography>
                      <Typography variant="body2">Equipment: ${est.equipment_cost.toLocaleString()}</Typography>
                      <Typography variant="body2">Overhead: ${est.overhead.toLocaleString()}</Typography>
                      <Typography variant="body2">Profit: ${est.profit.toLocaleString()}</Typography>
                      {est.confidence_score && (
                        <Typography variant="body2">Confidence: {est.confidence_score}%</Typography>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </List>
          </Paper>
        )}
      </Container>

      {loading && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'rgba(0,0,0,0.3)',
          }}
        >
          <CircularProgress />
        </Box>
      )}
    </Box>
  );
}
