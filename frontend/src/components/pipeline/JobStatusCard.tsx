import React, { useState } from 'react';
import { StatusBadge } from '../common/StatusBadge';
import { usePipeline } from '../../hooks/usePipeline';
import './JobStatusCard.css';

interface Job {
  id: number;
  name: string;
  status: string;
  stage?: string;
  ref?: string;
  started_at?: string;
  finished_at?: string;
  web_url?: string;
}

interface JobStatusCardProps {
  job: Job;
  sessionId: string;
}

export const JobStatusCard: React.FC = ({ job, sessionId }) => {
  const [showTrace, setShowTrace] = useState(false);
  const [trace, setTrace] = useState('');
  const [loadingTrace, setLoadingTrace] = useState(false);
  const { getJobTrace } = usePipeline(sessionId);

  const formatDuration = () => {
    if (!job.started_at) return null;

    const start = new Date(job.started_at);
    const end = job.finished_at ? new Date(job.finished_at) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor((diffMs % 60000) / 1000);

    return `${diffMins}m ${diffSecs}s`;
  };

  const handleShowTrace = async () => {
    if (showTrace) {
      setShowTrace(false);
      return;
    }

    setLoadingTrace(true);
    try {
      const jobTrace = await getJobTrace(job.id);
      setTrace(jobTrace);
      setShowTrace(true);
    } catch (error) {
      console.error('Failed to load job trace:', error);
      setTrace('Failed to load trace');
      setShowTrace(true);
    } finally {
      setLoadingTrace(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return '✅';
      case 'failed':
        return '❌';
      case 'running':
        return '🔄';
      case 'pending':
        return '⏳';
      case 'canceled':
        return '🚫';
      case 'skipped':
        return '⏭️';
      default:
        return '⚪';
    }
  };

  const getCardClass = () => {
    return `job-card ${job.status}`;
  };

  return (
    <div className={getCardClass()}>
      <header>
        <h3>{getStatusIcon(job.status)} {job.name}</h3>
      </header>
      <section>
        {job.stage && (
          <p>
            Stage:
            {job.stage}
          </p>
        )}
        {job.started_at && (
          <p>
            Started:
            <time dateTime={job.started_at}>{new Date(job.started_at).toLocaleTimeString()}</time>
          </p>
        )}
        {job.finished_at && (
          <p>
            Finished:
            <time dateTime={job.finished_at}>{new Date(job.finished_at).toLocaleTimeString()}</time>
          </p>
        )}
        {formatDuration() && (
          <p>
            Duration:
            {formatDuration()}
          </p>
        )}
      </section>
      <footer>
        <button onClick={handleShowTrace}>
          {loadingTrace ? '⏳' : showTrace ? '📄 Hide Trace' : '📄 Show Trace'}
        </button>
        {job.web_url && (
          <a href={job.web_url} target="_blank" rel="noopener noreferrer">
            🔗 GitLab
          </a>
        )}
      </footer>
      {showTrace && (
        <div className="trace-modal">
          <header>
            Job Trace
            <button onClick={() => setShowTrace(false)}>
              ✕
            </button>
          </header>
          <pre>{trace || 'No trace available'}</pre>
        </div>
      )}
    </div>
  );
};