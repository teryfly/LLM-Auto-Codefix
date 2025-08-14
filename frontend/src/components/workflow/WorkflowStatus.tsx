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
    merge_request?: any;
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
interface WorkflowStatusProps {
  status?: WorkflowStatusData | null;  // 允许为 null
  pipelineStatus?: PipelineStatusData | null;
}
export const WorkflowStatus: React.FC<WorkflowStatusProps> = ({
  status = null,
  pipelineStatus = null
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
  // 如果没有状态数据，显示占位符
  if (!status) {
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
    <div className="workflow-status">
      <div className="status-header">
        <h3>Workflow Status</h3>
        <StatusBadge status={status.status || 'unknown'} />
      </div>
      <div className="status-content">
        <div className="status-grid">
          <div className="status-card">
            <h4>General Information</h4>
            <div className="status-details">
              <div className="detail-item">
                <span className="detail-label">Session ID:</span>
                <span className="detail-value">
                  <code>{status.session_id || 'N/A'}</code>
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Status:</span>
                <span className="detail-value">
                  <StatusBadge status={status.status || 'unknown'} size="small" />
                  {status.status || 'Unknown'}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Current Step:</span>
                <span className="detail-value">{status.current_step || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Started:</span>
                <span className="detail-value">{formatDate(status.started_at)}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Last Updated:</span>
                <span className="detail-value">{formatDate(status.updated_at)}</span>
              </div>
              {getExecutionTime() && (
                <div className="detail-item">
                  <span className="detail-label">Execution Time:</span>
                  <span className="detail-value">{getExecutionTime()}</span>
                </div>
              )}
            </div>
          </div>
          {status.project_info && (
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
          {(status.pipeline_info || pipelineStatus) && (
            <div className="status-card">
              <h4>Pipeline Information</h4>
              <div className="status-details">
                {pipelineStatus?.pipeline_id && (
                  <div className="detail-item">
                    <span className="detail-label">Pipeline ID:</span>
                    <span className="detail-value">{pipelineStatus.pipeline_id}</span>
                  </div>
                )}
                {pipelineStatus?.status && (
                  <div className="detail-item">
                    <span className="detail-label">Pipeline Status:</span>
                    <span className="detail-value">
                      <StatusBadge status={pipelineStatus.status} size="small" />
                      {pipelineStatus.status}
                    </span>
                  </div>
                )}
                Code View
                {pipelineStatus?.ref && (
                  <div className="detail-item">
                    <span className="detail-label">Branch:</span>
                    <span className="detail-value">{pipelineStatus.ref}</span>
                  </div>
                )}
                {pipelineStatus?.web_url && (
                  <div className="detail-item">
                    <span className="detail-label">Pipeline URL:</span>
                    <span className="detail-value">
                      <a 
                        href={pipelineStatus.web_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="external-link"
                      >
                        View in GitLab 🔗
                      </a>
                    </span>
                  </div>
                )}
                {status.pipeline_info?.deployment_url && (
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
        </div>
        {status.error_message && (
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