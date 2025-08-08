import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { RecoilRoot } from 'recoil';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { Toaster } from 'react-hot-toast';
import ErrorBoundary from './components/ErrorBoundary';
import './i18n';
import './globals.css';
// @ts-ignore - Vercel Analytics has no type declaration yet
import { inject } from '@vercel/analytics';

// Run Vercel Web Analytics (no-op in dev)
inject();

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID as string}>
      <RecoilRoot>
        <QueryClientProvider client={new QueryClient()}>
          <BrowserRouter>
            <ErrorBoundary>
              <App />
            </ErrorBoundary>
          </BrowserRouter>
        </QueryClientProvider>
      </RecoilRoot>
      <Toaster position="top-center" />
    </GoogleOAuthProvider>
  </React.StrictMode>,
); 