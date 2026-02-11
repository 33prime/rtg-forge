/**
 * Good Vite+React app structure example.
 * Demonstrates lazy-loaded routes with error boundaries.
 */

import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { ErrorBoundary } from "@/components/error-boundary";
import { LoadingSpinner } from "@/components/loading-spinner";
import { RootLayout } from "@/layouts/root-layout";

// Lazy-loaded route components for code splitting
const DashboardPage = lazy(() => import("@/pages/dashboard"));
const InvoicesPage = lazy(() => import("@/pages/invoices"));
const InvoiceDetailPage = lazy(() => import("@/pages/invoice-detail"));
const SettingsPage = lazy(() => import("@/pages/settings"));

const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    errorElement: <ErrorBoundary />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <DashboardPage />
          </Suspense>
        ),
      },
      {
        path: "invoices",
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <InvoicesPage />
          </Suspense>
        ),
      },
      {
        path: "invoices/:id",
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <InvoiceDetailPage />
          </Suspense>
        ),
      },
      {
        path: "settings",
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <SettingsPage />
          </Suspense>
        ),
      },
    ],
  },
]);

export function App() {
  return <RouterProvider router={router} />;
}
