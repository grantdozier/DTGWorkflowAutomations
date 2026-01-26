import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Container,
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import QuoteComparison from '../../components/estimates/QuoteComparison';

export default function CompareQuotesPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const itemId = searchParams.get('itemId');

  return (
    <Box>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate(`/projects/${projectId}/quotes`)}
          >
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, ml: 2 }}>
            Compare Quotes
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <QuoteComparison projectId={projectId!} itemId={itemId || undefined} />
      </Container>
    </Box>
  );
}
