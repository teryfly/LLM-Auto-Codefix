import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { WorkflowDashboard } from './components/workflow/WorkflowDashboard';
import { PipelineMonitor } from './components/pipeline/PipelineMonitor';
import { ErrorBoundary } from './components/common/ErrorBoundary';

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <Layout />
    ),
    children: [
      {
        index: true,
        element: <WorkflowDashboard />,
      },
      {
        path: 'workflow/:sessionId',
        element: <WorkflowDashboard />,
      },
      {
        path: 'pipeline/:sessionId',
        element: <PipelineMonitor />,
      },
    ],
  },
]);

export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;