import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { FavoritesProvider } from './contexts/FavoritesContext';
import Header from './components/Header';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import OfficeDetailPage from './pages/OfficeDetailPage';
import ForecastPage from './pages/ForecastPage';
import AdminPage from './pages/AdminPage';
import ClientDashboard from './pages/ClientDashboard';
import FavoritesPage from './pages/FavoritesPage';

// Компонент для защиты маршрутов (требуется авторизация)
const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-state">Загрузка...</div>;
  }
  
  return user ? children : <Navigate to="/login" />;
};

// Компонент для проверки роли администратора
const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-state">Загрузка...</div>;
  }
  
  return user?.role_id === 1 ? children : <Navigate to="/dashboard" />;
};

// Компонент для проверки роли менеджера или администратора
const ManagerRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-state">Загрузка...</div>;
  }
  
  if (!user) return <Navigate to="/login" />;
  if (user.role_id !== 1 && user.role_id !== 2) {
    return <Navigate to="/client-dashboard" />;
  }
  return children;
};

function App() {
  return (
    <AuthProvider>
      <FavoritesProvider>
        <BrowserRouter>
          <Header />
          <Routes>
            {/* Публичные маршруты */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Защищённые маршруты */}
            <Route path="/dashboard" element={
              <PrivateRoute><DashboardPage /></PrivateRoute>
            } />
            
            <Route path="/office/:id" element={
              <PrivateRoute><OfficeDetailPage /></PrivateRoute>
            } />
            
            <Route path="/favorites" element={
              <PrivateRoute><FavoritesPage /></PrivateRoute>
            } />
            
            <Route path="/client-dashboard" element={
              <PrivateRoute><ClientDashboard /></PrivateRoute>
            } />
            
            <Route path="/forecast" element={
              <ManagerRoute><ForecastPage /></ManagerRoute>
            } />
            
            <Route path="/admin" element={
              <AdminRoute><AdminPage /></AdminRoute>
            } />
            
            {/* Корневой маршрут */}
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </Routes>
        </BrowserRouter>
      </FavoritesProvider>
    </AuthProvider>
  );
}

export default App;