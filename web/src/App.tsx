import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/contexts/AuthContext";
import { TutorialProvider } from "@/contexts/TutorialProvider";
import { TutorialPopup } from "@/components/tutorial/TutorialPopup";
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ApplicationDetailPage } from "@/pages/ApplicationDetailPage";
import { BatchReportPage } from "@/pages/BatchReportPage";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TutorialProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                element={
                  <ProtectedRoute>
                    <AppShell />
                  </ProtectedRoute>
                }
              >
                <Route path="/" element={<DashboardPage />} />
                <Route path="/applications/:id" element={<ApplicationDetailPage />} />
                <Route path="/batches/:id" element={<BatchReportPage />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
          <TutorialPopup />
          <Toaster />
        </TutorialProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
