import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';
import DashboardPage from './pages/DashboardPage';
import ProjectsPage from './pages/ProjectsPage';
import ChatPage from './pages/ChatPage';
import ReportsPage from './pages/ReportsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import TraceViewerPage from './pages/TraceViewerPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <Routes>
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:chatId" element={<ChatPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/traces" element={<TraceViewerPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Sign-in removed — any legacy /login or /register link lands in the app. */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
