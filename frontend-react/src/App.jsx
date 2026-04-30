// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { FavoritesProvider } from './contexts/FavoritesContext';
import Header from './components/Header';
import DashboardPage from './pages/DashboardPage';
import OfficeDetailPage from './pages/OfficeDetailPage';
import ForecastPage from './pages/ForecastPage';
import AdminPage from './pages/AdminPage';
import ClientDashboard from './pages/ClientDashboard';
import AuthPage from './pages/AuthPage';
import ManagerDashboard from './pages/ManagerDashboard';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-state">Загрузка...</div>;
  }
  
  return user ? children : <Navigate to="/auth" />;
};

const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-state">Загрузка...</div>;
  }
  
  return user?.role_id === 1 ? children : <Navigate to="/dashboard" />;
};

const ManagerRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-state">Загрузка...</div>;
  }
  
  if (!user) return <Navigate to="/auth" />;
  if (user.role_id !== 1 && user.role_id !== 2) {
    return <Navigate to="/client-dashboard" />;
  }
  return children;
};

const AppContent = () => {
  const location = useLocation();
  const hideHeader = location.pathname === '/auth';
  
  return (
    <>
      {!hideHeader && <Header />}
      <Routes>
        {/* ТОЛЬКО ЭТОТ ПУБЛИЧНЫЙ МАРШРУТ */}
        <Route path="/auth" element={<AuthPage />} />
        
        {/* ЗАЩИЩЁННЫЕ МАРШРУТЫ */}
        <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
        <Route path="/office/:id" element={<PrivateRoute><OfficeDetailPage /></PrivateRoute>} />
        <Route path="/client-dashboard" element={<PrivateRoute><ClientDashboard /></PrivateRoute>} />
        <Route path="/manager" element={<ManagerRoute><ManagerDashboard /></ManagerRoute>} />
        <Route path="/forecast" element={<ManagerRoute><ForecastPage /></ManagerRoute>} />
        <Route path="/admin" element={<AdminRoute><AdminPage /></AdminRoute>} />
        
        {/* РЕДИРЕКТ */}
        <Route path="/" element={<Navigate to="/dashboard" />} />
        
        {/* ВСЁ, ЧТО НЕ НАЙДЕНО — НА АВТОРИЗАЦИЮ */}
        <Route path="*" element={<Navigate to="/auth" />} />
      </Routes>
    </>
  );
};

function App() {
  return (
    <AuthProvider>
      <FavoritesProvider>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </FavoritesProvider>
    </AuthProvider>
  );
}

export default App;