import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { RootErrorBoundary } from '@/components/ErrorBoundary';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <RootErrorBoundary />,
    children: [
      {
        index: true,
        element: <Navigate to="/workflows" replace />
      },
      {
        path: 'workflows',
        lazy: () => import('@/pages/WorkflowsPage'),
      },
      {
        path: 'workflows/:id',
        lazy: () => import('@/pages/WorkflowDetailPage'),
      },
      {
        path: 'history',
        lazy: () => import('@/pages/HistoryPage'),
      },
      {
        path: 'logs',
        lazy: () => import('@/pages/LogsPage'),
      },
      {
        path: '*',
        element: <Navigate to="/workflows" replace />,
      },
    ],
  },
]);
