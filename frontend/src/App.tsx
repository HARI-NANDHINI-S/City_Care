import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { UserRole } from './types';
import { AnimatePresence } from 'framer-motion';

import { Layout } from './components/common/Layout';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ReportIssuePage } from './pages/ReportIssuePage';
import { PublicIssueMapPage } from './pages/PublicIssueMapPage';
import { MyReportsPage } from './pages/MyReportsPage';
import { IssueDetailsPage } from './pages/IssueDetailsPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { AdminIssueManagementPage } from './pages/AdminIssueManagementPage';
import { OfficerDashboardPage } from './pages/OfficerDashboardPage';
import { CitizenDashboardPage } from './pages/CitizenDashboardPage';
import { IssueTrackingPage } from './pages/IssueTrackingPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ModelIntelligencePage } from './pages/ModelIntelligencePage';

const ProtectedRoute: React.FC<{ children: React.ReactNode; roles?: UserRole[] }> = ({ children, roles }) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-10 h-10 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-400">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/map" replace />;
  }

  return <>{children}</>;
};

export const AppContent: React.FC = () => {
  return (
    <Layout>
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/map" element={<PublicIssueMapPage />} />
          <Route path="/issue/:id" element={<IssueDetailsPage />} />
          <Route path="/issue/:id/track" element={<ProtectedRoute roles={[UserRole.CITIZEN]}><IssueTrackingPage /></ProtectedRoute>} />

          {/* Citizen Routes */}
          <Route path="/dashboard" element={<ProtectedRoute roles={[UserRole.CITIZEN]}><CitizenDashboardPage /></ProtectedRoute>} />
          <Route path="/report" element={<ProtectedRoute roles={[UserRole.CITIZEN, UserRole.ADMIN]}><ReportIssuePage /></ProtectedRoute>} />
          <Route path="/my-reports" element={<ProtectedRoute roles={[UserRole.CITIZEN]}><MyReportsPage /></ProtectedRoute>} />

          {/* Admin Routes */}
          <Route path="/admin" element={<ProtectedRoute roles={[UserRole.ADMIN]}><AdminDashboardPage /></ProtectedRoute>} />
          <Route path="/admin/issues" element={<ProtectedRoute roles={[UserRole.ADMIN]}><AdminIssueManagementPage /></ProtectedRoute>} />
          <Route path="/admin/analytics" element={<ProtectedRoute roles={[UserRole.ADMIN]}><AnalyticsPage /></ProtectedRoute>} />
          <Route path="/model-intelligence" element={<ModelIntelligencePage />} />

          {/* Department Officer Routes */}
          <Route path="/officer" element={<ProtectedRoute roles={[UserRole.OFFICER]}><OfficerDashboardPage /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </Layout>
  );
};

export const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
};

export default App;
