import React, { useState } from 'react';
import { JobStatusCard } from './JobStatusCard';
import { PipelineGraph } from './PipelineGraph';
import { usePipeline } from '../../hooks/usePipeline';
import { usePolling } from '../../hooks/usePolling';
import { StatusBadge } from '../common/StatusBadge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import './PipelineMonitor.css';

interface PipelineMonitorProps {
  sessionId: string;
}

export const PipelineMonitor: React.FC = ({ sessionId }) => {
  const [viewMode, setViewMode] = useState('cards');
  const { isPolling, pollingConfig } = usePolling();

  const {
    pipelineStatus,
    jobStatuses,
    monitorData,
    isLoading,
    error,
    retryFailedJobs
  } = usePipeline(sessionId);

  const handleRetryJobs = async () => {
    try {
      await retryFailedJobs();
    } catch (error) {
      console.error('Failed to retry jobs:', error);
    }
  };

  if (isLoading && !pipelineStatus) {
    return (
       <div className="loading-spinner">
        <LoadingSpinner /> Loading pipeline data...
       </div>
    );
  }

  if (error) {
    return (
      <div className="error-message">
        <h2>Error Loading Pipeline</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()} className="btn btn-primary">
          Retry
        </button>
      </div>
    );
  }

  if (!pipelineStatus) {
    return (
      <div className="no-data">
        <h2>No Pipeline Data</h2>
        <p>No pipeline information available for this session.</p>
      </div>
    );
  }

  const failedJobs = jobStatuses.filter(job => job.status === 'failed');
  const runningJobs = jobStatuses.filter(job => job.status === 'running');

  return (
    <div className="pipeline-monitor">
      <header>
        <h1>Pipeline Monitor</h1>
        <p>
          Pipeline #{pipelineStatus.pipeline_id}
          {pipelineStatus.ref && (
            <span>Branch: {pipelineStatus.ref}</span>
          )}
        </p>
      </header>

      <div className="controls">
        <button onClick={() => setViewMode('cards')}>
          📋 Cards
        </button>
        <button onClick={() => setViewMode('graph')}>
          📊 Graph
        </button>

        {failedJobs.length > 0 && (
          <button onClick={handleRetryJobs}>
            🔄 Retry Failed ({failedJobs.length})
          </button>
        )}

        <div className="polling-status">
          <span>{isPolling ? '🔄' : '⏸️'}</span>
          <span>{isPolling ? 'Live' : 'Paused'}</span>
        </div>
      </div>

      {monitorData?.summary && (
        <div className="summary">
          <p>Total Jobs: {monitorData.summary.total_jobs}</p>
          <p>Completed: {monitorData.summary.completed_jobs}</p>
          <p>Failed: {monitorData.summary.failed_jobs}</p>
          <p>Progress: {monitorData.summary.progress_percent.toFixed(1)}%</p>
        </div>
      )}

      <div className="job-statuses">
        {viewMode === 'cards' ? (
          <div className="card-view">
            {jobStatuses.length === 0 ? (
              <p>No jobs found for this pipeline.</p>
            ) : (
              jobStatuses.map((job) => (
                <JobStatusCard key={job.id} job={job} />
              ))
            )}
          </div>
        ) : (
          <PipelineGraph jobs={jobStatuses} />
        )}
      </div>

      {pipelineStatus.web_url && (
        <a href={pipelineStatus.web_url} target="_blank" rel="noopener noreferrer">
          🔗 View in GitLab
        </a>
      )}
    </div>
  );
};