import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./stores/authStore";
import Layout from "./components/layout/Layout";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import AdminRoute from "./components/layout/AdminRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import ArbitragePage from "./pages/ArbitragePage";
import ItemDetailPage from "./pages/ItemDetailPage";
import MarketplacesPage from "./pages/MarketplacesPage";
import AdminDashboard from "./pages/admin/AdminDashboard";
import InviteCodesPage from "./pages/admin/InviteCodesPage";
import UsersPage from "./pages/admin/UsersPage";

export default function App() {
  const loadFromStorage = useAuthStore((s) => s.loadFromStorage);

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/arbitrage" element={<ArbitragePage />} />
          <Route path="/items/:itemId" element={<ItemDetailPage />} />
          <Route path="/marketplaces" element={<MarketplacesPage />} />

          <Route element={<AdminRoute />}>
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/invite-codes" element={<InviteCodesPage />} />
            <Route path="/admin/users" element={<UsersPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
