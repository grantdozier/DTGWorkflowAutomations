import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  ArrowBack,
  Description,
  Article,
  Build,
  Calculate,
  Warning,
  Info,
  Receipt,
} from '@mui/icons-material';
import { getProject } from '../services/api';
import Layout from '../components/Layout';

// Tab components (will be created)
import OverviewTab from '../components/projects/OverviewTab';
import DocumentsTab from '../components/projects/DocumentsTab';
import TakeoffsTab from '../components/projects/TakeoffsTab';
import SpecificationsTab from '../components/projects/SpecificationsTab';
import QuotesTab from '../components/projects/QuotesTab';
import EstimatesTab from '../components/projects/EstimatesTab';
import DiscrepanciesTab from '../components/projects/DiscrepanciesTab';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ProjectDetail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<any>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [documentCount, setDocumentCount] = useState(0);
  const [takeoffCount, setTakeoffCount] = useState(0);
  const [specCount, setSpecCount] = useState(0);
  const [quoteCount, setQuoteCount] = useState(0);
  const [discrepancyCount, setDiscrepancyCount] = useState(0);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    try {
      setLoading(true);
      const response = await getProject(projectId!);
      setProject(response.data);
      setError('');
    } catch (err: any) {
      console.error('Failed to load project', err);
      setError(err.response?.data?.detail || 'Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const updateCounts = (counts: {
    documents?: number;
    takeoffs?: number;
    specs?: number;
    quotes?: number;
    discrepancies?: number;
  }) => {
    if (counts.documents !== undefined) setDocumentCount(counts.documents);
    if (counts.takeoffs !== undefined) setTakeoffCount(counts.takeoffs);
    if (counts.specs !== undefined) setSpecCount(counts.specs);
    if (counts.quotes !== undefined) setQuoteCount(counts.quotes);
    if (counts.discrepancies !== undefined) setDiscrepancyCount(counts.discrepancies);
  };

  if (loading) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  if (error || !project) {
    return (
      <Layout>
        <Container maxWidth="lg" sx={{ mt: 4 }}>
          <Alert severity="error">{error || 'Project not found'}</Alert>
          <Button onClick={() => navigate('/dashboard')} sx={{ mt: 2 }}>
            Back to Dashboard
          </Button>
        </Container>
      </Layout>
    );
  }

  return (
    <Layout>
      {/* Project sub-header */}
      <Box sx={{ bgcolor: 'grey.100', borderBottom: '1px solid', borderColor: 'grey.300', py: 1.5, px: { xs: 2, md: 4 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/dashboard')}
            size="small"
            sx={{ color: 'grey.700' }}
          >
            Back
          </Button>
          <Typography variant="h6" sx={{ fontWeight: 600, color: 'grey.900' }}>{project.name}</Typography>
          <Typography variant="body2" color="text.secondary">
            Job #{project.job_number} • {project.location || 'No location'}
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Button
            variant="outlined"
            size="small"
            onClick={() => navigate(`/projects/${projectId}/quotes`)}
          >
            Manage Quotes
          </Button>
          <Chip
            label={project.status || 'Active'}
            color={project.status === 'completed' ? 'success' : 'primary'}
            size="small"
          />
        </Box>
      </Box>

      <Paper sx={{ mx: 2, mt: -1, borderRadius: '8px 8px 0 0' }} elevation={0}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="project tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab
            icon={<Info />}
            iconPosition="start"
            label="Overview"
            id="project-tab-0"
            aria-controls="project-tabpanel-0"
          />
          <Tab
            icon={<Article />}
            iconPosition="start"
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Documents
                {documentCount > 0 && (
                  <Chip label={documentCount} size="small" color="primary" />
                )}
              </Box>
            }
            id="project-tab-1"
            aria-controls="project-tabpanel-1"
          />
          <Tab
            icon={<Build />}
            iconPosition="start"
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Takeoffs
                {takeoffCount > 0 && (
                  <Chip label={takeoffCount} size="small" color="primary" />
                )}
              </Box>
            }
            id="project-tab-2"
            aria-controls="project-tabpanel-2"
          />
          <Tab
            icon={<Description />}
            iconPosition="start"
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Specifications
                {specCount > 0 && (
                  <Chip label={specCount} size="small" color="primary" />
                )}
              </Box>
            }
            id="project-tab-3"
            aria-controls="project-tabpanel-3"
          />
          <Tab
            icon={<Receipt />}
            iconPosition="start"
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Quotes
                {quoteCount > 0 && (
                  <Chip label={quoteCount} size="small" color="primary" />
                )}
              </Box>
            }
            id="project-tab-4"
            aria-controls="project-tabpanel-4"
          />
          <Tab
            icon={<Calculate />}
            iconPosition="start"
            label="Estimates"
            id="project-tab-5"
            aria-controls="project-tabpanel-5"
          />
          <Tab
            icon={<Warning />}
            iconPosition="start"
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Discrepancies
                {discrepancyCount > 0 && (
                  <Chip label={discrepancyCount} size="small" color="error" />
                )}
              </Box>
            }
            id="project-tab-6"
            aria-controls="project-tabpanel-6"
          />
        </Tabs>
      </Paper>

      <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
        <TabPanel value={activeTab} index={0}>
          <OverviewTab project={project} onProjectUpdate={loadProject} />
        </TabPanel>
        <TabPanel value={activeTab} index={1}>
          <DocumentsTab
            projectId={projectId!}
            onCountUpdate={(count) => updateCounts({ documents: count })}
          />
        </TabPanel>
        <TabPanel value={activeTab} index={2}>
          <TakeoffsTab
            projectId={projectId!}
            onCountUpdate={(count) => updateCounts({ takeoffs: count })}
          />
        </TabPanel>
        <TabPanel value={activeTab} index={3}>
          <SpecificationsTab
            projectId={projectId!}
            onCountUpdate={(count) => updateCounts({ specs: count })}
          />
        </TabPanel>
        <TabPanel value={activeTab} index={4}>
          <QuotesTab
            projectId={projectId!}
            onCountUpdate={(count) => updateCounts({ quotes: count })}
          />
        </TabPanel>
        <TabPanel value={activeTab} index={5}>
          <EstimatesTab projectId={projectId!} />
        </TabPanel>
        <TabPanel value={activeTab} index={6}>
          <DiscrepanciesTab
            projectId={projectId!}
            onCountUpdate={(count) => updateCounts({ discrepancies: count })}
          />
        </TabPanel>
      </Container>
    </Layout>
  );
}
