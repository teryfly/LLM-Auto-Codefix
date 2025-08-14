import React, { useState, useEffect } from 'react';
import { usePolling } from '../../hooks/usePolling';
import { LoadingSpinner } from '../common/LoadingSpinner';
import './LogViewer.css';

interface LogViewerProps {
  sessionId: string;
}

export const LogViewer: React.FC = ({ sessionId }) => {
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const { isPolling } = usePolling();

  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/v1/workflow/logs/${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch logs');
      }
      const data = await response.json();
      setLogs(data.logs || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();

    if (isPolling) {
      const interval = setInterval(fetchLogs, 5000);
      return () => clearInterval(interval);
    }
  }, [sessionId, isPolling]);

  useEffect(() => {
    if (autoScroll) {
      const logContainer = document.querySelector('.log-content');
      if (logContainer) {
        logContainer.scrollTop = logContainer.scrollHeight;
      }
    }
  }, [logs, autoScroll]);

  return (
     <div className="log-viewer">
       <header>
         <h2>Workflow Logs</h2>
         <div className="controls">
           <label>
             <input type="checkbox" checked={autoScroll} onChange={(e) => setAutoScroll(e.target.checked)} />
             Auto-scroll
           </label>
           <button onClick={fetchLogs}>🔄 Refresh</button>
         </div>
       </header>
      {error && (
        <div className="error">Error: {error}</div>
      )}
      <div className="log-content">
        {isLoading && logs.length === 0 ? (
          <LoadingSpinner />
        ) : logs.length === 0 ? (
          <div>No logs available</div>
        ) : (
          <pre>{logs.map((log, index) => (
            <div key={index}>{log}</div>
          ))}</pre>
        )}
      </div>
    </div>
  );
};