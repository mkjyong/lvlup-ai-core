import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';

const AuthPage = lazy(() => import('./pages/AuthPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const BillingPage = lazy(() => import('./pages/BillingPage'));
const HomePage = lazy(() => import('./pages/HomePage'));
const OnboardingWizard = lazy(() => import('./pages/OnboardingWizard'));
const PerformancePage = lazy(() => import('./pages/PerformancePage'));
const TermsPage = lazy(() => import('./pages/TermsPage'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'));

const App: React.FC = () => (
  <Suspense fallback={<div className="flex h-screen items-center justify-center">Loading...</div>}>
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route element={<ProtectedRoute />}> 
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/dashboard/performance" element={<PerformancePage />} />
        <Route path="/billing" element={<BillingPage />} />
        <Route path="/onboarding" element={<OnboardingWizard />} />
      </Route>
      <Route path="/*" element={<Navigate to="/" replace />} />
    </Routes>
  </Suspense>
);

export default App; 