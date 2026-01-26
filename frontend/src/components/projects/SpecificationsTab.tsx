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
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Link,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  Add,
  Delete,
  OpenInNew,
  Search as SearchIcon,
  CheckCircle,
  Help,
} from '@mui/icons-material';
import api from '../../services/api';

interface Props {
  projectId: string;
  onCountUpdate: (count: number) => void;
}

interface Specification {
  id: string;
  spec_code: string;
  title: string;
  source?: string;
  confidence_score?: number;
  context?: string;
  library_id?: string;
  description?: string;
}

export default function SpecificationsTab({ projectId, onCountUpdate }: Props) {
  const [specs, setSpecs] = useState<Specification[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [openAdd, setOpenAdd] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    loadSpecifications();
  }, [projectId]);

  const loadSpecifications = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/projects/${projectId}/specs`);
      const specsList = response.data.specifications || response.data || [];
      setSpecs(specsList);
      onCountUpdate(specsList.length);
    } catch (err) {
      console.error('Failed to load specifications', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);
      const response = await api.get(`/specifications/search`, {
        params: { query: searchQuery, limit: 10 },
      });
      setSearchResults(response.data);
    } catch (err: any) {
      console.error('Failed to search specifications', err);
      setError(err.response?.data?.detail || 'Failed to search specifications');
    } finally {
      setSearching(false);
    }
  };

  const handleAddSpec = async (specCode: string, libraryId?: string) => {
    try {
      await api.post(`/projects/${projectId}/specs`, {
        spec_code: specCode,
        library_id: libraryId,
      });
      setMessage('Specification added successfully');
      setTimeout(() => setMessage(''), 2000);
      await loadSpecifications();
      setOpenAdd(false);
      setSearchQuery('');
      setSearchResults([]);
    } catch (err: any) {
      console.error('Failed to add specification', err);
      setError(err.response?.data?.detail || 'Failed to add specification');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/projects/${projectId}/specs/${id}`);
      setMessage('Specification removed');
      setTimeout(() => setMessage(''), 2000);
      await loadSpecifications();
    } catch (err: any) {
      console.error('Failed to delete specification', err);
      setError(err.response?.data?.detail || 'Failed to delete specification');
    }
  };

  const getConfidenceChip = (score?: number) => {
    if (!score) return null;
    let color: 'success' | 'warning' | 'error' = 'success';
    let label = 'High';

    if (score < 0.5) {
      color = 'error';
      label = 'Low';
    } else if (score < 0.75) {
      color = 'warning';
      label = 'Medium';
    }

    return <Chip label={`${label} (${Math.round(score * 100)}%)`} color={color} size="small" />;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Specifications</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setOpenAdd(true)}>
          Add Specification
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
        ) : specs.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Help sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No specifications added
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Specifications are automatically extracted when parsing documents, or you can add them
              manually
            </Typography>
          </Box>
        ) : (
          <List>
            {specs.map((spec) => (
              <ListItem key={spec.id} divider>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {spec.spec_code}
                      </Typography>
                      {spec.library_id && (
                        <CheckCircle fontSize="small" color="success" titleAccess="Matched to library" />
                      )}
                      {getConfidenceChip(spec.confidence_score)}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2">{spec.title}</Typography>
                      {spec.context && (
                        <Typography variant="caption" color="text.secondary">
                          Context: {spec.context}
                        </Typography>
                      )}
                      {spec.description && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {spec.description}
                        </Typography>
                      )}
                      {spec.source && (
                        <Chip label={spec.source} size="small" sx={{ mt: 0.5 }} />
                      )}
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {spec.library_id && (
                      <IconButton
                        edge="end"
                        size="small"
                        onClick={() => {
                          // Open spec details or external link
                          window.open(
                            `https://standards.org/spec/${spec.spec_code}`,
                            '_blank'
                          );
                        }}
                      >
                        <OpenInNew />
                      </IconButton>
                    )}
                    <IconButton
                      edge="end"
                      size="small"
                      color="error"
                      onClick={() => handleDelete(spec.id)}
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}
      </Paper>

      {/* Add Specification Dialog */}
      <Dialog open={openAdd} onClose={() => setOpenAdd(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add Specification</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', gap: 1, mt: 2, mb: 3 }}>
            <TextField
              label="Search by code or title"
              placeholder="e.g., ASTM-C150, ACI 301"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              fullWidth
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSearch();
                }
              }}
            />
            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
              disabled={searching || !searchQuery.trim()}
            >
              Search
            </Button>
          </Box>

          {searching && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          )}

          {searchResults.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Search Results
              </Typography>
              <List>
                {searchResults.map((result) => (
                  <ListItem key={result.id} divider>
                    <ListItemText
                      primary={`${result.spec_code} - ${result.title}`}
                      secondary={result.description}
                    />
                    <ListItemSecondaryAction>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleAddSpec(result.spec_code, result.id)}
                      >
                        Add
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {!searching && searchQuery && searchResults.length === 0 && (
            <Alert severity="info">
              No specifications found. You can still add it manually by entering the code.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAdd(false)}>Cancel</Button>
          <Button
            onClick={() => handleAddSpec(searchQuery)}
            variant="contained"
            disabled={!searchQuery.trim()}
          >
            Add Manually
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
