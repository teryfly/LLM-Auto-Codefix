import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { WorkflowDashboard } from './components/workflow/WorkflowDashboard';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { useConfig } from './hooks/useConfig';
import './App.css';
const App: React.FC = () => {
  const { config, loading, error } = useConfig();
  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading configuration...</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="app-error">
        <h1>Configuration Error</h1>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }
  return (
    <ErrorBoundary>
      <Router>
        <div className="App">
          <Layout>
            <Routes>
              <Route path="/" element={<WorkflowDashboard />} />
              <Route path="/workflow/:sessionId" element={<WorkflowDashboard />} />
              <Route path="/pipeline/:sessionId" element={<WorkflowDashboard />} />
              <Route path="*" element={<WorkflowDashboard />} />
            </Routes>
          </Layout>
        </div>
      </Router>
    </ErrorBoundary>
  );
};
export default App;