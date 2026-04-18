import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Header from './components/Header';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import OfficeDetailPage from './pages/OfficeDetailPage';
import ForecastPage from './pages/ForecastPage';
import AdminPage from './pages/AdminPage';
import ClientDashboard from './pages/ClientDashboard';


const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div>Загрузка...</div>; // Показываем загрузку, пока проверяем
  }
  
  return user ? children : <Navigate to="/login" />;
};

const AdminRoute = ({ children }) => {
  const { user } = useAuth();
  return user?.role_id === 1 ? children : <Navigate to="/login" />;
};

const ManagerRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (user.role_id !== 1 && user.role_id !== 2) {
    return <Navigate to="/client-dashboard" />;
  }
  return children;
};
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Header />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/office/:id" element={<OfficeDetailPage />} />
          <Route path="/forecast" element={
            <ManagerRoute><ForecastPage /></ManagerRoute>
          } />
          <Route path="/admin" element={
            <AdminRoute><AdminPage /></AdminRoute>
          } />
          <Route path="/client-dashboard" element={
            <PrivateRoute><ClientDashboard /></PrivateRoute>
          } />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;