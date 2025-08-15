import React from 'react';
import { StatusBadge } from '../common/StatusBadge';
import './WorkflowStatus.css';
interface WorkflowStatusData {
  session_id?: string;
  status?: string;
  current_step?: string;
  project_info?: {
    project_name?: string;
    project_id?: number;
    local_dir?: string;
  };
  pipeline_info?: {
    pipeline_id?: number;
    merge_request?: {
      id?: number;
      iid?: number;
      web_url?: string;
      title?: string;
    };
    deployment_url?: string;
  };
  error_message?: string;
  started_at?: string;
  updated_at?: string;
}
interface PipelineStatusData {
  pipeline_id?: number;
  status?: string;
  ref?: string;
  web_url?: string;
}
interface CIStatusData {
  merge_request: {
    id: number;
    iid: number;
    title: string;
    state: string;
    source_branch: string;
    target_branch: string;
    web_url: string;
  };
  pipeline?: {
    id: number;
    status: string;
    ref: string;
    web_url: string;
    created_at?: string;
    updated_at?: string;
  };
  jobs: Array<{
    id: number;
    name: string;
    status: string;
    stage: string;
    started_at?: string;
    finished_at?: string;
    web_url?: string;
  }>;
  overall_status: string;
}
interface WorkflowStatusProps {
  status?: WorkflowStatusData | null;
  pipelineStatus?: PipelineStatusData | null;
  ciStatus?: CIStatusData | null;
  isRecovered?: boolean;
  mrExists?: boolean | null;
  shouldStopPolling?: boolean;
}
export const WorkflowStatus: React.FC<WorkflowStatusProps> = ({
  status = null,
  pipelineStatus = null,
  ciStatus = null,
  isRecovered = false,
  mrExists = null,
  shouldStopPolling = false
}) => {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return 'Invalid Date';
    }
  };
  const getExecutionTime = () => {
    if (!status?.started_at) return null;
    try {
      const start = new Date(status.started_at);
      const end = status.updated_at ? new Date(status.updated_at) : new Date();
      const diffMs = end.getTime() - start.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffSecs = Math.floor((diffMs % 60000) / 1000);
      return `${diffMins}m ${diffSecs}s`;
    } catch {
      return 'N/A';
    }
  };
  // 计算Job统计信息
  const getJobStats = () => {
    if (!ciStatus?.jobs || ciStatus.jobs.length === 0) {
      return null;
    }
    const total = ciStatus.jobs.length;
    const completed = ciStatus.jobs.filter(job => 
      ['success', 'failed', 'canceled', 'skipped'].includes(job.status)
    ).length;
    const failed = ciStatus.jobs.filter(job => job.status === 'failed').length;
    const running = ciStatus.jobs.filter(job => 
      ['running', 'pending'].includes(job.status)
    ).length;
    return { total, completed, failed, running };
  };
  const jobStats = getJobStats();
  // 如果MR不存在，显示错误状态
  if (mrExists === false) {
    return (
      <div className="workflow-status">
        <div className="status-header">
          <h3>Workflow Status</h3>
          <StatusBadge status="failed" />
        </div>
        <div className="error-card">
          <h4>Merge Request Not Found</h4>
          <div className="error-content">
            <span className="error-icon">❌</span>
            <span className="error-text">
              The specified Merge Request could not be found. Please verify the MR ID and project name.
            </span>
          </div>
        </div>
      </div>
    );
  }
  // 如果没有状态数据，显示占位符
  if (!status && !ciStatus) {
    return (
      <div className="workflow-status">
        <div className="status-header">
          <h3>Workflow Status</h3>
          <StatusBadge status="unknown" />
        </div>
        <div className="status-content">
          <div className="status-placeholder">
            <p>No workflow data available. Start a workflow to see status information.</p>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className={`workflow-status ${isRecovered ? 'recovered-status' : ''}`}>
      <div className="status-header">
        <h3>Workflow Status</h3>
        <div className="status-badges">
          <StatusBadge status={status?.status || ciStatus?.overall_status || 'unknown'} />
          {isRecovered && (
            <span className="recovery-status-badge">
              🔄 Recovered
            </span>
          )}
          {shouldStopPolling && (
            <span className="polling-status-badge">
              ⏹️ Monitoring Stopped
            </span>
          )}
        </div>
      </div>
      {isRecovered && (
        <div className="recovery-notice-status">
          <div className="notice-content">
            <span className="notice-icon">🔍</span>
            <div className="notice-text">
              <strong>Status Recovery Mode:</strong> This workflow status has been recovered 
              from GitLab MR information. The system is actively checking CI/CD progress 
              to provide real-time updates.
            </div>
          </div>
        </div>
      )}
      <div className="status-content">
        <div className="status-grid">
          <div className="status-card">
            <h4>General Information</h4>
            <div className="status-details">
              <div className="detail-item">
                <span className="detail-label">Session ID:</span>
                <span className="detail-value">
                  <code>{status?.session_id || 'N/A'}</code>
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Status:</span>
                <span className="detail-value">
                  <StatusBadge status={status?.status || ciStatus?.overall_status || 'unknown'} size="small" />
                  {status?.status || ciStatus?.overall_status || 'Unknown'}
                  {isRecovered && <span className="recovery-suffix"> (Recovered)</span>}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Current Step:</span>
                <span className="detail-value">{status?.current_step || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Started:</span>
                <span className="detail-value">{formatDate(status?.started_at)}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Last Updated:</span>
                <span className="detail-value">{formatDate(status?.updated_at)}</span>
              </div>
              {getExecutionTime() && (
                <div className="detail-item">
                  <span className="detail-label">Execution Time:</span>
                  <span className="detail-value">{getExecutionTime()}</span>
                </div>
              )}
            </div>
          </div>
          {status?.project_info && (
            <div className="status-card">
              <h4>Project Information</h4>
              <div className="status-details">
                <div className="detail-item">
                  <span className="detail-label">Project Name:</span>
                  <span className="detail-value">{status.project_info.project_name || 'N/A'}</span>
                </div>
                {status.project_info.project_id && (
                  <div className="detail-item">
                    <span className="detail-label">Project ID:</span>
                    <span className="detail-value">{status.project_info.project_id}</span>
                  </div>
                )}
                {status.project_info.local_dir && (
                  <div className="detail-item">
                    <span className="detail-label">Local Directory:</span>
                    <span className="detail-value">
                      <code>{status.project_info.local_dir}</code>
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
          {(ciStatus?.pipeline || pipelineStatus) && (
            <div className="status-card">
              <h4>Pipeline Information</h4>
              <div className="status-details">
                <div className="detail-item">
                  <span className="detail-label">Pipeline ID:</span>
                  <span className="detail-value">
                    {ciStatus?.pipeline?.id || pipelineStatus?.pipeline_id || 'N/A'}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Pipeline Status:</span>
                  <span className="detail-value">
                    <StatusBadge 
                      status={ciStatus?.pipeline?.status || pipelineStatus?.status || 'unknown'} 
                      size="small" 
                    />
                    {ciStatus?.pipeline?.status || pipelineStatus?.status || 'Unknown'}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Branch:</span>
                  <span className="detail-value">
                    {ciStatus?.pipeline?.ref || pipelineStatus?.ref || 'N/A'}
                  </span>
                </div>
                {(ciStatus?.pipeline?.web_url || pipelineStatus?.web_url) && (
                  <div className="detail-item">
                    <span className="detail-label">Pipeline URL:</span>
                    <span className="detail-value">
                      <a 
                        href={ciStatus?.pipeline?.web_url || pipelineStatus?.web_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="external-link"
                      >
                        View in GitLab 🔗
                      </a>
                    </span>
                  </div>
                )}
                {status?.pipeline_info?.deployment_url && (
                  <div className="detail-item">
                    <span className="detail-label">Deployment URL:</span>
                    <span className="detail-value">
                      <a 
                        href={status.pipeline_info.deployment_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="external-link deployment-link"
                      >
                        🚀 View Deployment
                      </a>
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
          {(ciStatus?.merge_request || status?.pipeline_info?.merge_request) && (
            <div className="status-card mr-info-card">
              <h4>Merge Request Information</h4>
              <div className="status-details">
                <div className="detail-item">
                  <span className="detail-label">MR ID:</span>
                  <span className="detail-value">
                    <code className="mr-id">
                      {ciStatus?.merge_request?.iid || status?.pipeline_info?.merge_request?.iid || 
                       ciStatus?.merge_request?.id || status?.pipeline_info?.merge_request?.id}
                    </code>
                  </span>
                </div>
                {(ciStatus?.merge_request?.title || status?.pipeline_info?.merge_request?.title) && (
                  <div className="detail-item">
                    <span className="detail-label">Title:</span>
                    <span className="detail-value">
                      {ciStatus?.merge_request?.title || status?.pipeline_info?.merge_request?.title}
                    </span>
                  </div>
                )}
                {ciStatus?.merge_request?.state && (
                  <div className="detail-item">
                    <span className="detail-label">State:</span>
                    <span className="detail-value">
                      <StatusBadge status={ciStatus.merge_request.state} size="small" />
                      {ciStatus.merge_request.state}
                    </span>
                  </div>
                )}
                {(ciStatus?.merge_request?.source_branch && ciStatus?.merge_request?.target_branch) && (
                  <div className="detail-item">
                    <span className="detail-label">Branches:</span>
                    <span className="detail-value">
                      {ciStatus.merge_request.source_branch} → {ciStatus.merge_request.target_branch}
                    </span>
                  </div>
                )}
                {(ciStatus?.merge_request?.web_url || status?.pipeline_info?.merge_request?.web_url) && (
                  <div className="detail-item">
                    <span className="detail-label">MR URL:</span>
                    <span className="detail-value">
                      <a 
                        href={ciStatus?.merge_request?.web_url || status?.pipeline_info?.merge_request?.web_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="external-link mr-link"
                      >
                        View MR in GitLab 🔗
                      </a>
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
          {jobStats && (
            <div className="status-card">
              <h4>CI/CD Jobs Summary</h4>
              <div className="status-details">
                <div className="detail-item">
                  <span className="detail-label">Total Jobs:</span>
                  <span className="detail-value">{jobStats.total}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Completed:</span>
                  <span className="detail-value">{jobStats.completed}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Failed:</span>
                  <span className="detail-value">
                    <span className={jobStats.failed > 0 ? 'text-danger' : ''}>
                      {jobStats.failed}
                    </span>
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Running:</span>
                  <span className="detail-value">{jobStats.running}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Progress:</span>
                  <span className="detail-value">
                    {Math.round((jobStats.completed / jobStats.total) * 100)}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
        {status?.error_message && (
          <div className="error-card">
            <h4>Error Details</h4>
            <div className="error-content">
              <span className="error-icon">⚠️</span>
              <span className="error-text">{status.error_message}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};