import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Upload,
  AutoAwesome,
  Visibility,
  Download,
  Delete,
  PictureAsPdf,
} from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  projectId: string;
  onCountUpdate: (count: number) => void;
}

interface Document {
  id: string;
  file_name: string;
  doc_type: string;
  uploaded_at: string;
  file_path: string;
  is_parsed: boolean;
}

export default function DocumentsTab({ projectId, onCountUpdate }: Props) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, [projectId]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/documents`);
      setDocuments(response.data);
      onCountUpdate(response.data.length);
    } catch (err) {
      console.error('Failed to load documents', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError('');
    setMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', 'plan');

      await api.post(`/projects/${projectId}/documents`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setMessage('Document uploaded successfully');
      setTimeout(() => setMessage(''), 3000);
      await loadDocuments();
    } catch (err: any) {
      console.error('Failed to upload document', err);
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleParseDocument = async (documentId: string) => {
    setParsing(documentId);
    setError('');
    setMessage('');

    try {
      const response = await api.post(`/ai/parse-document`, {
        project_id: projectId,
        document_id: documentId,
      });

      setMessage(
        `Successfully parsed! Extracted ${response.data.items_saved || 0} items`
      );
      setTimeout(() => setMessage(''), 3000);
      await loadDocuments();
    } catch (err: any) {
      console.error('Failed to parse document', err);
      setError(err.response?.data?.detail || 'Failed to parse document');
    } finally {
      setParsing(null);
    }
  };

  const handleDownload = async (doc: Document) => {
    try {
      const response = await api.get(
        `/projects/${projectId}/documents/${doc.id}`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = window.document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.file_name || `document_${doc.id}.pdf`);
      window.document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Failed to download document', err);
      if (err.response?.status === 404) {
        setError('File not found. This may be a sample document without an actual file.');
      } else {
        setError('Failed to download document');
      }
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;

    try {
      await api.delete(`/projects/${projectId}/documents/${deleteConfirm}`);
      setMessage('Document deleted successfully');
      setTimeout(() => setMessage(''), 3000);
      await loadDocuments();
      setDeleteConfirm(null);
    } catch (err: any) {
      console.error('Failed to delete document', err);
      setError(err.response?.data?.detail || 'Failed to delete document');
      setDeleteConfirm(null);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Documents</Typography>
        <Button
          variant="contained"
          component="label"
          startIcon={<Upload />}
          disabled={uploading}
        >
          {uploading ? 'Uploading...' : 'Upload Document'}
          <input
            type="file"
            hidden
            accept=".pdf"
            onChange={handleFileUpload}
            disabled={uploading}
          />
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

      <Paper>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : documents.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <PictureAsPdf sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No documents uploaded
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Upload a PDF plan to get started with AI-powered takeoff extraction
            </Typography>
          </Box>
        ) : (
          <List>
            {documents.map((doc, index) => (
              <Box key={doc.id}>
                <ListItem>
                  <Box sx={{ mr: 2 }}>
                    <PictureAsPdf color="error" />
                  </Box>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {doc.file_name}
                        {doc.is_parsed && (
                          <Chip label="Parsed" color="success" size="small" />
                        )}
                      </Box>
                    }
                    secondary={`Uploaded ${new Date(doc.uploaded_at).toLocaleString()} • ${
                      doc.doc_type
                    }`}
                  />
                  <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <IconButton
                        edge="end"
                        aria-label="view"
                        size="small"
                        onClick={() => window.open(`/api/v1/projects/${projectId}/documents/${doc.id}`, '_blank')}
                      >
                        <Visibility />
                      </IconButton>
                      <IconButton
                        edge="end"
                        aria-label="download"
                        size="small"
                        onClick={() => handleDownload(doc)}
                      >
                        <Download />
                      </IconButton>
                      {!doc.is_parsed && (
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={
                            parsing === doc.id ? (
                              <CircularProgress size={16} />
                            ) : (
                              <AutoAwesome />
                            )
                          }
                          onClick={() => handleParseDocument(doc.id)}
                          disabled={parsing === doc.id}
                        >
                          Parse with AI
                        </Button>
                      )}
                      <IconButton
                        edge="end"
                        aria-label="delete"
                        size="small"
                        color="error"
                        onClick={() => setDeleteConfirm(doc.id)}
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < documents.length - 1 && <Box sx={{ borderBottom: 1, borderColor: 'divider' }} />}
              </Box>
            ))}
          </List>
        )}
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this document? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirm(null)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
