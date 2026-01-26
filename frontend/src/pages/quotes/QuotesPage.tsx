import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import QuoteManager from '../../components/estimates/QuoteManager';

export default function QuotesPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

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
            Quote Management
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <QuoteManager projectId={projectId!} />
      </Container>
    </Box>
  );
}
