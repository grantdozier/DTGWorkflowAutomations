import { Navigate, useLocation } from 'react-router-dom';
import { CircularProgress, Box } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: JSX.Element;
  requiresOnboarding?: boolean;
}

export default function ProtectedRoute({ children, requiresOnboarding = false }: ProtectedRouteProps) {
  const { isAuthenticated, isOnboardingComplete, loading } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking auth status
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Authenticated but requires onboarding and not completed
  if (requiresOnboarding && !isOnboardingComplete) {
    // Don't redirect if already on onboarding page
    if (location.pathname !== '/onboarding') {
      return <Navigate to="/onboarding" state={{ from: location }} replace />;
    }
  }

  // Authenticated and onboarding complete - don't allow access to onboarding
  if (isOnboardingComplete && location.pathname === '/onboarding') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
