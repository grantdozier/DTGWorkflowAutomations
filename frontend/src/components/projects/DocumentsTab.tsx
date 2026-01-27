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
  Tabs,
  Tab,
} from '@mui/material';
import {
  Upload,
  AutoAwesome,
  Visibility,
  Download,
  Delete,
  PictureAsPdf,
  Description,
  Article,
  Folder,
} from '@mui/icons-material';
import api from '../../services/api';
import ParsingProgressDialog from './ParsingProgressDialog';

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
  const [activeTab, setActiveTab] = useState(0);
  const [parsingProgress, setParsingProgress] = useState({
    open: false,
    documentName: '',
    status: 'idle' as 'idle' | 'converting' | 'tiling' | 'analyzing' | 'extracting' | 'saving' | 'complete' | 'error',
    progress: 0,
    currentPage: 0,
    totalPages: 0,
    itemsExtracted: 0,
    error: '',
  });

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

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    docType: 'plan' | 'spec' | 'plan_and_spec' | 'addendum'
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError('');
    setMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', docType);

      await api.post(`/projects/${projectId}/documents`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setMessage(`${docType === 'plan' ? 'Plan' : docType === 'spec' ? 'Specification' : 'Document'} uploaded successfully`);
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
    const doc = documents.find(d => d.id === documentId);
    setParsing(documentId);
    setError('');
    setMessage('');
    
    // Show progress dialog
    setParsingProgress({
      open: true,
      documentName: doc?.file_name || 'Document',
      status: 'converting',
      progress: 10,
      currentPage: 1,
      totalPages: 5,
      itemsExtracted: 0,
      error: '',
    });

    try {
      // Simulate progress stages
      setTimeout(() => setParsingProgress(p => ({ ...p, status: 'analyzing', progress: 40 })), 2000);
      setTimeout(() => setParsingProgress(p => ({ ...p, status: 'extracting', progress: 70 })), 5000);
      
      const response = await api.post(
        `/ai/projects/${projectId}/documents/${documentId}/parse-and-save`
      );

      const itemsSaved = response.data.items_saved || 0;
      
      // Show completion
      setParsingProgress(p => ({
        ...p,
        status: 'complete',
        progress: 100,
        itemsExtracted: itemsSaved,
      }));
      
      setMessage(
        `Successfully parsed! Extracted ${itemsSaved} items`
      );
      setTimeout(() => {
        setMessage('');
        setParsingProgress(p => ({ ...p, open: false }));
      }, 3000);
      await loadDocuments();
    } catch (err: any) {
      console.error('Failed to parse document', err);
      const errorDetail = err.response?.data?.detail || 'Failed to parse document';
      
      setParsingProgress(p => ({
        ...p,
        status: 'error',
        error: errorDetail,
      }));
      
      if (errorDetail.includes('No AI services')) {
        setError('AI services not configured. Please add ANTHROPIC_API_KEY or OPENAI_API_KEY to your .env file.');
      } else {
        setError(errorDetail);
      }
      
      setTimeout(() => setParsingProgress(p => ({ ...p, open: false })), 5000);
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

  // Filter documents by type
  const planDocuments = documents.filter((d) => d.doc_type === 'plan');
  const specDocuments = documents.filter((d) => d.doc_type === 'spec');
  const planAndSpecDocuments = documents.filter((d) => d.doc_type === 'plan_and_spec');
  const otherDocuments = documents.filter(
    (d) => d.doc_type !== 'plan' && d.doc_type !== 'spec' && d.doc_type !== 'plan_and_spec'
  );

  // Render document list for a specific type
  const renderDocumentList = (
    docs: Document[],
    emptyMessage: string,
    emptyDescription: string
  ) => {
    if (loading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      );
    }

    if (docs.length === 0) {
      return (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <PictureAsPdf sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {emptyMessage}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {emptyDescription}
          </Typography>
        </Box>
      );
    }

    return (
      <List>
        {docs.map((doc, index) => (
          <Box key={doc.id}>
            <ListItem>
              <Box sx={{ mr: 2 }}>
                {doc.doc_type === 'spec' ? (
                  <Article color="primary" />
                ) : (
                  <PictureAsPdf color="error" />
                )}
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
                    onClick={() =>
                      window.open(
                        `/api/v1/projects/${projectId}/documents/${doc.id}`,
                        '_blank'
                      )
                    }
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
            {index < docs.length - 1 && (
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }} />
            )}
          </Box>
        ))}
      </List>
    );
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3 }}>
        Documents
      </Typography>

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
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            icon={<Description />}
            label={`Plans (${planDocuments.length})`}
            iconPosition="start"
          />
          <Tab
            icon={<Article />}
            label={`Specifications (${specDocuments.length})`}
            iconPosition="start"
          />
          <Tab
            icon={<Description />}
            label={`Plan & Spec (${planAndSpecDocuments.length})`}
            iconPosition="start"
          />
          <Tab
            icon={<Folder />}
            label={`Other (${otherDocuments.length})`}
            iconPosition="start"
          />
        </Tabs>

        {/* PLANS TAB */}
        {activeTab === 0 && (
          <Box>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="subtitle1" fontWeight="bold">
                    Construction Plans
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Vision-based parsing with intelligent tiling for microscopic detail
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  component="label"
                  startIcon={<Upload />}
                  disabled={uploading}
                >
                  {uploading ? 'Uploading...' : 'Upload Plan'}
                  <input
                    type="file"
                    hidden
                    accept=".pdf"
                    onChange={(e) => handleFileUpload(e, 'plan')}
                    disabled={uploading}
                  />
                </Button>
              </Box>
            </Box>
            {renderDocumentList(
              planDocuments,
              'No plans uploaded',
              'Upload construction plans for AI-powered takeoff extraction with vision models'
            )}
          </Box>
        )}

        {/* SPECIFICATIONS TAB */}
        {activeTab === 1 && (
          <Box>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="subtitle1" fontWeight="bold">
                    Specifications
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Text extraction and intelligent structuring for specification documents
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  component="label"
                  startIcon={<Upload />}
                  disabled={uploading}
                  color="primary"
                >
                  {uploading ? 'Uploading...' : 'Upload Spec'}
                  <input
                    type="file"
                    hidden
                    accept=".pdf"
                    onChange={(e) => handleFileUpload(e, 'spec')}
                    disabled={uploading}
                  />
                </Button>
              </Box>
            </Box>
            {renderDocumentList(
              specDocuments,
              'No specifications uploaded',
              'Upload specification documents for text extraction and requirement analysis'
            )}
          </Box>
        )}

        {/* PLAN & SPEC COMBINED TAB */}
        {activeTab === 2 && (
          <Box>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="subtitle1" fontWeight="bold">
                    Plan & Specification Combined
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Documents containing both construction plans and specifications
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  component="label"
                  startIcon={<Upload />}
                  disabled={uploading}
                  color="secondary"
                >
                  {uploading ? 'Uploading...' : 'Upload Plan & Spec'}
                  <input
                    type="file"
                    hidden
                    accept=".pdf"
                    onChange={(e) => handleFileUpload(e, 'plan_and_spec')}
                    disabled={uploading}
                  />
                </Button>
              </Box>
            </Box>
            {renderDocumentList(
              planAndSpecDocuments,
              'No combined documents uploaded',
              'Upload documents that contain both plans and specifications'
            )}
          </Box>
        )}

        {/* OTHER/ADDENDUM TAB */}
        {activeTab === 3 && (
          <Box>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="subtitle1" fontWeight="bold">
                    Other Documents
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Addenda, photos, and other project documents
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  component="label"
                  startIcon={<Upload />}
                  disabled={uploading}
                  color="secondary"
                >
                  {uploading ? 'Uploading...' : 'Upload Document'}
                  <input
                    type="file"
                    hidden
                    accept=".pdf"
                    onChange={(e) => handleFileUpload(e, 'addendum')}
                    disabled={uploading}
                  />
                </Button>
              </Box>
            </Box>
            {renderDocumentList(
              otherDocuments,
              'No other documents uploaded',
              'Upload addenda, photos, or other project-related documents'
            )}
          </Box>
        )}
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this document? This action cannot be
            undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirm(null)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Parsing Progress Dialog */}
      <ParsingProgressDialog
        open={parsingProgress.open}
        documentName={parsingProgress.documentName}
        onClose={() => setParsingProgress(p => ({ ...p, open: false }))}
        status={parsingProgress.status}
        progress={parsingProgress.progress}
        currentPage={parsingProgress.currentPage}
        totalPages={parsingProgress.totalPages}
        itemsExtracted={parsingProgress.itemsExtracted}
        error={parsingProgress.error}
      />
    </Box>
  );
}
