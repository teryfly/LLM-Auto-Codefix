import React from 'react';
import { StatusBadge } from '../common/StatusBadge';
import './ProjectInfo.css';
interface WorkflowStatus {
  session_id?: string;
  status?: string;
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
  started_at?: string;
  updated_at?: string;
}
interface ProjectInfoProps {
  workflowStatus?: WorkflowStatus | null;
  onViewPipeline?: (projectName: string) => void;
}
export const ProjectInfo: React.FC<ProjectInfoProps> = ({
  workflowStatus,
  onViewPipeline
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
    if (!workflowStatus?.started_at) return null;
    try {
      const start = new Date(workflowStatus.started_at);
      const end = workflowStatus.updated_at ? new Date(workflowStatus.updated_at) : new Date();
      const diffMs = end.getTime() - start.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffSecs = Math.floor((diffMs % 60000) / 1000);
      return `${diffMins}m ${diffSecs}s`;
    } catch {
      return 'N/A';
    }
  };
  const handleViewPipeline = () => {
    if (workflowStatus?.project_info?.project_name && onViewPipeline) {
      onViewPipeline(workflowStatus.project_info.project_name);
    }
  };
  if (!workflowStatus) {
    return (
      <div className="project-info">
        <h3>Project Information</h3>
        <div className="no-project-info">
          <p>No project information available.</p>
          <p>Start a workflow to see project details.</p>
        </div>
      </div>
    );
  }
  return (
    <div className="project-info">
      <div className="info-header">
        <h3>Project Information</h3>
        {workflowStatus.status && (
          <StatusBadge status={workflowStatus.status} size="small" />
        )}
      </div>
      <div className="info-content">
        {/* 基本信息 */}
        <div className="info-section">
          <h4>Basic Info</h4>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Project Name:</span>
              <span className="info-value">
                {workflowStatus.project_info?.project_name || 'N/A'}
              </span>
            </div>
            {workflowStatus.project_info?.project_id && (
              <div className="info-item">
                <span className="info-label">Project ID:</span>
                <span className="info-value">{workflowStatus.project_info.project_id}</span>
              </div>
            )}
            <div className="info-item">
              <span className="info-label">Status:</span>
              <span className="info-value">
                <StatusBadge status={workflowStatus.status || 'unknown'} size="small" />
              </span>
            </div>
          </div>
        </div>
        {/* 时间信息 */}
        <div className="info-section">
          <h4>Timing</h4>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Started:</span>
              <span className="info-value">{formatDate(workflowStatus.started_at)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Last Updated:</span>
              <span className="info-value">{formatDate(workflowStatus.updated_at)}</span>
            </div>
            {getExecutionTime() && (
              <div className="info-item">
                <span className="info-label">Duration:</span>
                <span className="info-value">{getExecutionTime()}</span>
              </div>
            )}
          </div>
        </div>
        {/* Pipeline 信息 */}
        {workflowStatus.pipeline_info && (
          <div className="info-section">
            <h4>Pipeline Info</h4>
            <div className="info-grid">
              {workflowStatus.pipeline_info.pipeline_id && (
                <div className="info-item">
                  <span className="info-label">Pipeline ID:</span>
                  <span className="info-value">{workflowStatus.pipeline_info.pipeline_id}</span>
                </div>
              )}
              {workflowStatus.pipeline_info.merge_request && (
                <div className="info-item">
                  <span className="info-label">Merge Request:</span>
                  <span className="info-value">
                    #{workflowStatus.pipeline_info.merge_request.iid || workflowStatus.pipeline_info.merge_request.id}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
        {/* 操作按钮 */}
        <div className="info-actions">
          {workflowStatus.project_info?.project_name && (
            <button
              onClick={handleViewPipeline}
              className="btn btn-primary btn-small"
            >
              📊 View Project Pipeline
            </button>
          )}
          {workflowStatus.pipeline_info?.merge_request?.web_url && (
            <a
              href={workflowStatus.pipeline_info.merge_request.web_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary btn-small"
            >
              🔗 View MR in GitLab
            </a>
          )}
          {workflowStatus.pipeline_info?.deployment_url && (
            <a
              href={workflowStatus.pipeline_info.deployment_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-success btn-small"
            >
              🚀 View Deployment
            </a>
          )}
        </div>
      </div>
    </div>
  );
};