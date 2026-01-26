import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'

// Context
import { AuthProvider } from './contexts/AuthContext'

// Components
import ProtectedRoute from './components/ProtectedRoute'

// Pages
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ProjectDetail from './pages/ProjectDetail'
import OnboardingPage from './pages/onboarding/OnboardingPage'
import EquipmentSettings from './pages/settings/EquipmentSettings'
import VendorSettings from './pages/settings/VendorSettings'
import SettingsPage from './pages/settings/SettingsPage'
import QuotesPage from './pages/quotes/QuotesPage'
import RequestQuotesPage from './pages/quotes/RequestQuotesPage'
import CompareQuotesPage from './pages/quotes/CompareQuotesPage'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1e40af',
      light: '#3b82f6',
      dark: '#1e3a8a',
    },
    secondary: {
      main: '#0891b2',
      light: '#22d3ee',
      dark: '#0e7490',
    },
    background: {
      default: '#f1f5f9',
      paper: '#ffffff',
    },
    grey: {
      50: '#f8fafc',
      100: '#f1f5f9',
      200: '#e2e8f0',
      300: '#cbd5e1',
      400: '#94a3b8',
      500: '#64748b',
      600: '#475569',
      700: '#334155',
      800: '#1e293b',
      900: '#0f172a',
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: '#1e40af',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
          '&:hover': {
            boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
        },
        contained: {
          boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
  shape: {
    borderRadius: 8,
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 600,
    },
  },
})

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Onboarding Route (requires auth but not onboarding complete) */}
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute>
                  <OnboardingPage />
                </ProtectedRoute>
              }
            />

            {/* Protected Routes (require auth AND onboarding complete) */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute requiresOnboarding>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/project/:projectId"
              element={
                <ProtectedRoute requiresOnboarding>
                  <ProjectDetail />
                </ProtectedRoute>
              }
            />

            {/* Quote Management Routes */}
            <Route
              path="/projects/:projectId/quotes"
              element={
                <ProtectedRoute requiresOnboarding>
                  <QuotesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/:projectId/request-quotes"
              element={
                <ProtectedRoute requiresOnboarding>
                  <RequestQuotesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/:projectId/compare-quotes"
              element={
                <ProtectedRoute requiresOnboarding>
                  <CompareQuotesPage />
                </ProtectedRoute>
              }
            />

            {/* Settings Routes */}
            <Route
              path="/settings"
              element={
                <ProtectedRoute requiresOnboarding>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings/equipment"
              element={
                <ProtectedRoute requiresOnboarding>
                  <EquipmentSettings />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings/vendors"
              element={
                <ProtectedRoute requiresOnboarding>
                  <VendorSettings />
                </ProtectedRoute>
              }
            />

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
