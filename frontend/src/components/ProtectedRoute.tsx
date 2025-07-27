import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Layout from './Layout';

const ProtectedRoute: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const onboarded = localStorage.getItem('onboarded') === 'true';

  if (!isAuthenticated) return <Navigate to="/auth" replace />;
  if (!onboarded && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  return <Layout />;
};

export default ProtectedRoute; 