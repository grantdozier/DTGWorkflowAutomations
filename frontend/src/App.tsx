import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
})

function HomePage() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          DTG Workflow Automations
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          Construction Estimation & Project Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome to the DTG Workflow Automations platform. This system helps you manage
          construction projects, estimates, and workflows efficiently.
        </Typography>
      </Box>
    </Container>
  )
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App
