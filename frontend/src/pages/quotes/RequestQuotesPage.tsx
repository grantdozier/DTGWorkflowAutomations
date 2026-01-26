import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import QuoteRequestForm from '../../components/estimates/QuoteRequestForm';

export default function RequestQuotesPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const handleComplete = () => {
    navigate(`/projects/${projectId}/quotes`);
  };

  const handleCancel = () => {
    navigate(`/projects/${projectId}`);
  };

  return (
    <Box>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate(`/projects/${projectId}`)}
          >
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, ml: 2 }}>
            Request Quotes
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <QuoteRequestForm
          projectId={projectId!}
          onComplete={handleComplete}
          onCancel={handleCancel}
        />
      </Container>
    </Box>
  );
}
