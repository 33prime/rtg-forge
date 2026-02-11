/**
 * BAD Vite+React app structure example.
 *
 * Problems:
 * - No lazy loading — entire app in one bundle
 * - No error boundaries
 * - No loading states
 * - All routes eagerly imported
 */

import { BrowserRouter, Route, Routes } from "react-router-dom";
import { DashboardPage } from "./pages/dashboard";     // Eager import
import { InvoicesPage } from "./pages/invoices";         // Eager import
import { InvoiceDetailPage } from "./pages/invoice-detail"; // Eager import
import { SettingsPage } from "./pages/settings";         // Eager import

// No error boundary, no suspense, no code splitting
export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/invoices" element={<InvoicesPage />} />
        <Route path="/invoices/:id" element={<InvoiceDetailPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        {/* No catch-all 404 route */}
      </Routes>
    </BrowserRouter>
  );
}
