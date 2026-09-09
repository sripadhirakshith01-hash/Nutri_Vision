import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { AppLayout } from "./layouts/AppLayout";
import { PublicLayout } from "./layouts/PublicLayout";
import { AnalyzePage } from "./pages/Analyze";
import { AnalyticsPage } from "./pages/Analytics";
import { ChatPage } from "./pages/Chat";
import { DashboardPage } from "./pages/Dashboard";
import { HomePage } from "./pages/Home";
import { LoginPage } from "./pages/Login";
import { MealsPage } from "./pages/Meals";
import { ProfilePage } from "./pages/Profile";
import { RegisterPage } from "./pages/Register";

function PublicOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="skeleton mx-auto mt-24 h-40 w-96 rounded-3xl" />;
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route path="/" element={<HomePage />} />
          </Route>
          <Route
            path="/login"
            element={
              <PublicOnly>
                <LoginPage />
              </PublicOnly>
            }
          />
          <Route
            path="/register"
            element={
              <PublicOnly>
                <RegisterPage />
              </PublicOnly>
            }
          />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/analyze" element={<AnalyzePage />} />
              <Route path="/meals" element={<MealsPage />} />
              <Route path="/diary" element={<Navigate to="/meals" replace />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/insights" element={<Navigate to="/analytics" replace />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
