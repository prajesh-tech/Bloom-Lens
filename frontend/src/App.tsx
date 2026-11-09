import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { Layout } from './components/layout/Layout';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { RequireSession } from './components/layout/RequireSession';
const Home = lazy(() => import('./pages/Home').then((module) => ({ default: module.Home })));
const Analyze = lazy(() => import('./pages/Analyze').then((module) => ({ default: module.Analyze })));
const AnalysisResults = lazy(() => import('./pages/AnalysisResults').then((module) => ({ default: module.AnalysisResults })));
const History = lazy(() => import('./pages/History').then((module) => ({ default: module.History })));
const Settings = lazy(() => import('./pages/Settings').then((module) => ({ default: module.Settings })));
const Login = lazy(() => import('./pages/Login').then((module) => ({ default: module.Login })));
const Analytics = lazy(() => import('./pages/Analytics').then((module) => ({ default: module.Analytics })));

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <ErrorBoundary>
          <Suspense fallback={<p role="status" className="p-8">Loading page…</p>}><Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<RequireSession />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Home />} />
              <Route path="analyze" element={<Analyze />} />
              <Route path="analysis/:id" element={<AnalysisResults />} />
              <Route path="history" element={<History />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="settings" element={<Settings />} />
            </Route>
            </Route>
          </Routes></Suspense>
        </ErrorBoundary>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
