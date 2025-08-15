import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { StatusBadge } from '../common/StatusBadge';
import { usePolling } from '../../hooks/usePolling';
import { projectPipelineApi } from '../../services/project-pipeline-api';
import './JobLogView.css';
interface Job {
  id: number;
  name: string;
  status: string;
  stage: string;
  ref?: string;
  started_at?: string;
  finished_at?: string;
  web_url?: string;
}
interface Project {
  id: number;
  name: string;
  path_with_namespace: string;
  web_url: string;
}
export const JobLogView: React.FC = () => {
  const { projectName, jobId } = useParams<{ 
    projectName: string; 
    jobId: string; 
  }>();
  const navigate = useNavigate();
  const { isPolling } = usePolling();
  const [project, setProject] = useState<Project | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [logs, setLogs] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const actualProjectName = projectName?.replace('-', '/') || '';
  const jobIdNum = jobId ? parseInt(jobId) : 0;
  const fetchProjectInfo = async () => {
    try {
      const projectData = await projectPipelineApi.getProjectInfo(actualProjectName);
      setProject(projectData);
      return projectData;
    } catch (err) {
      console.error('Failed to fetch project info:', err);
      throw new Error(`Project '${actualProjectName}' not found`);
    }
  };
  const fetchJobInfo = async (projectId: number, jobIdNum: number) => {
    try {
      const jobData = await projectPipelineApi.getJob(projectId, jobIdNum);
      setJob(jobData);
      return jobData;
    } catch (err) {
      console.error('Failed to fetch job info:', err);
      throw new Error(`Job ${jobIdNum} not found`);
    }
  };
  const fetchJobLogs = async (projectId: number, jobIdNum: number) => {
    try {
      const logsData = await projectPipelineApi.getJobTrace(projectId, jobIdNum);
      setLogs(logsData);
      return logsData;
    } catch (err) {
      console.error('Failed to fetch job logs:', err);
      return 'Failed to load job logs.';
    }
  };
  const loadJobData = async () => {
    if (!actualProjectName || !jobIdNum) return;
    try {
      setIsLoading(true);
      setError(null);
      // 1. 获取项目信息
      const projectData = await fetchProjectInfo();
      // 2. 获取 Job 信息
      const jobData = await fetchJobInfo(projectData.id, jobIdNum);
      // 3. 获取 Job 日志
      const logsData = await fetchJobLogs(projectData.id, jobIdNum);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load job data';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };
  // 初始加载
  useEffect(() => {
    loadJobData();
  }, [actualProjectName, jobIdNum]);
  // 轮询更新（仅对运行中的 Job）
  useEffect(() => {
    if (isPolling && project && job && ['running', 'pending'].includes(job.status)) {
      const interval = setInterval(async () => {
        try {
          // 更新 Job 状态
          const updatedJob = await fetchJobInfo(project.id, jobIdNum);
          // 更新日志
          const updatedLogs = await fetchJobLogs(project.id, jobIdNum);
        } catch (err) {
          console.error('Failed to update job data:', err);
        }
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isPolling, project, job, jobIdNum]);
  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && logs) {
      const logContainer = document.querySelector('.log-content');
      if (logContainer) {
        logContainer.scrollTop = logContainer.scrollHeight;
      }
    }
  }, [logs, autoScroll]);
  const handleGoBack = () => {
    if (projectName) {
      navigate(`/${projectName}/pipeline`);
    } else {
      navigate(-1);
    }
  };
  const formatDuration = () => {
    if (!job?.started_at) return null;
    const start = new Date(job.started_at);
    const end = job.finished_at ? new Date(job.finished_at) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor((diffMs % 60000) / 1000);
    return `${diffMins}m ${diffSecs}s`;
  };
  if (isLoading && !job) {
    return (
      <div className="job-log-loading">
        <LoadingSpinner />
        <p>Loading job logs for {actualProjectName}...</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="job-log-error">
        <h2>Error Loading Job</h2>
        <p>{error}</p>
        <div className="error-actions">
          <button onClick={loadJobData} className="btn btn-primary">
            Retry
          </button>
          <button onClick={handleGoBack} className="btn btn-secondary">
            Go Back
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="job-log-view">
      <div className="job-header">
        <div className="header-content">
          <div className="breadcrumb">
            <button onClick={handleGoBack} className="breadcrumb-link">
              ← {actualProjectName}
            </button>
            <span className="breadcrumb-separator">/</span>
            <span className="breadcrumb-current">Job #{jobIdNum}</span>
          </div>
          {job && (
            <div className="job-info">
              <h1>{job.name}</h1>
              <div className="job-meta">
                <StatusBadge status={job.status} />
                <span className="job-stage">Stage: {job.stage}</span>
                {formatDuration() && (
                  <span className="job-duration">Duration: {formatDuration()}</span>
                )}
              </div>
            </div>
          )}
        </div>
        <div className="header-actions">
          <label className="auto-scroll-toggle">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>
          <button onClick={loadJobData} className="btn btn-secondary">
            🔄 Refresh
          </button>
          {job?.web_url && (
            <a
              href={job.web_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
            >
              GitLab 🔗
            </a>
          )}
        </div>
      </div>
      {job && (
        <div className="job-details-card">
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">Status:</span>
              <StatusBadge status={job.status} />
            </div>
            <div className="detail-item">
              <span className="detail-label">Stage:</span>
              <span className="detail-value">{job.stage}</span>
            </div>
            {job.ref && (
              <div className="detail-item">
                <span className="detail-label">Branch:</span>
                <span className="detail-value">{job.ref}</span>
              </div>
            )}
            {job.started_at && (
              <div className="detail-item">
                <span className="detail-label">Started:</span>
                <span className="detail-value">{new Date(job.started_at).toLocaleString()}</span>
              </div>
            )}
            {job.finished_at && (
              <div className="detail-item">
                <span className="detail-label">Finished:</span>
                <span className="detail-value">{new Date(job.finished_at).toLocaleString()}</span>
              </div>
            )}
            {formatDuration() && (
              <div className="detail-item">
                <span className="detail-label">Duration:</span>
                <span className="detail-value">{formatDuration()}</span>
              </div>
            )}
          </div>
        </div>
      )}
      <div className="logs-container">
        <div className="logs-header">
          <h3>Job Logs</h3>
          <div className="logs-controls">
            <span className="logs-info">
              {logs.split('\n').length} lines
            </span>
          </div>
        </div>
        <div className="log-content">
          {logs ? (
            <pre className="log-text">{logs}</pre>
          ) : (
            <div className="no-logs">
              <p>No logs available for this job.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};