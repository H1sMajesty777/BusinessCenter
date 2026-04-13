import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import OfficeDetailPage from './pages/OfficeDetailPage';
import ForecastPage from './pages/ForecastPage';
import ContractsPage from './pages/ContractsPage';
import AdminPage from './pages/AdminPage';

const PrivateRoute = ({ children }) => {
  const user = localStorage.getItem('user');
  return user ? children : <Navigate to="/login" />;
};

const AdminRoute = ({ children }) => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  return user.role_id === 1 ? children : <Navigate to="/dashboard" />;
};

function App() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={
          <PrivateRoute><DashboardPage /></PrivateRoute>
        } />
        <Route path="/office/:id" element={
          <PrivateRoute><OfficeDetailPage /></PrivateRoute>
        } />
        <Route path="/forecast" element={
          <PrivateRoute><ForecastPage /></PrivateRoute>
        } />
        <Route path="/contracts" element={
          <PrivateRoute><ContractsPage /></PrivateRoute>
        } />
        <Route path="/admin" element={
          <AdminRoute><AdminPage /></AdminRoute>
        } />
        <Route path="/" element={<Navigate to="/dashboard" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;