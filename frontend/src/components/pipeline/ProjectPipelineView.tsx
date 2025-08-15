import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { StatusBadge } from '../common/StatusBadge';
import { usePolling } from '../../hooks/usePolling';
import { projectPipelineApi } from '../../services/project-pipeline-api';
import './ProjectPipelineView.css';
interface Pipeline {
  id: number;
  status: string;
  ref: string;
  sha: string;
  web_url?: string;
  created_at?: string;
  updated_at?: string;
}
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
  default_branch: string;
}
export const ProjectPipelineView: React.FC = () => {
  const { projectName, pipelineId } = useParams<{ 
    projectName: string; 
    pipelineId?: string; 
  }>();
  const navigate = useNavigate();
  const { isPolling } = usePolling();
  const [project, setProject] = useState<Project | null>(null);
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const actualProjectName = projectName?.replace('-', '/') || '';
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
  const fetchLatestPipeline = async (projectId: number) => {
    try {
      const pipelines = await projectPipelineApi.getLatestPipeline(projectId);
      if (pipelines && pipelines.length > 0) {
        return pipelines[0];
      }
      return null;
    } catch (err) {
      console.error('Failed to fetch pipeline:', err);
      return null;
    }
  };
  const fetchSpecificPipeline = async (projectId: number, pipelineIdNum: number) => {
    try {
      return await projectPipelineApi.getPipeline(projectId, pipelineIdNum);
    } catch (err) {
      console.error('Failed to fetch specific pipeline:', err);
      throw new Error(`Pipeline ${pipelineIdNum} not found`);
    }
  };
  const fetchPipelineJobs = async (projectId: number, pipelineIdNum: number) => {
    try {
      return await projectPipelineApi.getPipelineJobs(projectId, pipelineIdNum);
    } catch (err) {
      console.error('Failed to fetch pipeline jobs:', err);
      return [];
    }
  };
  const loadPipelineData = async () => {
    if (!actualProjectName) return;
    try {
      setIsLoading(true);
      setError(null);
      // 1. 获取项目信息
      const projectData = await fetchProjectInfo();
      // 2. 获取 Pipeline
      let pipelineData: Pipeline | null = null;
      if (pipelineId) {
        // 获取指定的 Pipeline
        pipelineData = await fetchSpecificPipeline(projectData.id, parseInt(pipelineId));
      } else {
        // 获取最新的 Pipeline
        pipelineData = await fetchLatestPipeline(projectData.id);
      }
      if (!pipelineData) {
        throw new Error('No pipeline found for this project');
      }
      setPipeline(pipelineData);
      // 3. 获取 Pipeline 下的所有 Jobs
      const jobsData = await fetchPipelineJobs(projectData.id, pipelineData.id);
      setJobs(jobsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load pipeline data';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };
  // 初始加载
  useEffect(() => {
    loadPipelineData();
  }, [actualProjectName, pipelineId]);
  // 轮询更新
  useEffect(() => {
    if (isPolling && project && pipeline) {
      const interval = setInterval(async () => {
        try {
          // 更新 Pipeline 状态
          const updatedPipeline = await fetchSpecificPipeline(project.id, pipeline.id);
          setPipeline(updatedPipeline);
          // 更新 Jobs 状态
          const updatedJobs = await fetchPipelineJobs(project.id, pipeline.id);
          setJobs(updatedJobs);
        } catch (err) {
          console.error('Failed to update pipeline data:', err);
        }
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isPolling, project, pipeline]);
  const handleJobClick = (job: Job) => {
    if (projectName) {
      navigate(`/${projectName}/job/${job.id}/logs`);
    }
  };
  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'success': return '#28a745';
      case 'failed': return '#dc3545';
      case 'running': return '#007bff';
      case 'pending': return '#ffc107';
      case 'canceled': return '#6c757d';
      case 'skipped': return '#6c757d';
      default: return '#e9ecef';
    }
  };
  const groupJobsByStage = (jobs: Job[]) => {
    const stages: Record<string, Job[]> = {};
    jobs.forEach(job => {
      const stage = job.stage || 'unknown';
      if (!stages[stage]) {
        stages[stage] = [];
      }
      stages[stage].push(job);
    });
    return stages;
  };
  if (isLoading && !pipeline) {
    return (
      <div className="project-pipeline-loading">
        <LoadingSpinner />
        <p>Loading pipeline data for {actualProjectName}...</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="project-pipeline-error">
        <h2>Error Loading Pipeline</h2>
        <p>{error}</p>
        <button onClick={loadPipelineData} className="btn btn-primary">
          Retry
        </button>
      </div>
    );
  }
  const jobsByStage = groupJobsByStage(jobs);
  const stageNames = Object.keys(jobsByStage);
  return (
    <div className="project-pipeline-view">
      <div className="pipeline-header">
        <div className="header-content">
          <h1>Pipeline: {actualProjectName}</h1>
          {project && (
            <div className="project-info">
              <p><strong>Project:</strong> {project.path_with_namespace}</p>
              <p><strong>Default Branch:</strong> {project.default_branch}</p>
              {project.web_url && (
                <a href={project.web_url} target="_blank" rel="noopener noreferrer" className="external-link">
                  View in GitLab 🔗
                </a>
              )}
            </div>
          )}
        </div>
        <div className="header-actions">
          <button onClick={loadPipelineData} className="btn btn-secondary">
            🔄 Refresh
          </button>
        </div>
      </div>
      {pipeline && (
        <div className="pipeline-info-card">
          <h3>Pipeline #{pipeline.id}</h3>
          <div className="pipeline-details">
            <div className="detail-item">
              <span className="detail-label">Status:</span>
              <StatusBadge status={pipeline.status} />
            </div>
            <div className="detail-item">
              <span className="detail-label">Branch:</span>
              <span className="detail-value">{pipeline.ref}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">SHA:</span>
              <span className="detail-value">{pipeline.sha.substring(0, 8)}</span>
            </div>
            {pipeline.created_at && (
              <div className="detail-item">
                <span className="detail-label">Created:</span>
                <span className="detail-value">{new Date(pipeline.created_at).toLocaleString()}</span>
              </div>
            )}
            {pipeline.web_url && (
              <div className="detail-item">
                <span className="detail-label">GitLab URL:</span>
                <a href={pipeline.web_url} target="_blank" rel="noopener noreferrer" className="external-link">
                  View Pipeline 🔗
                </a>
              </div>
            )}
          </div>
        </div>
      )}
      <div className="jobs-container">
        <h3>Jobs ({jobs.length})</h3>
        {stageNames.length === 0 ? (
          <div className="no-jobs">
            <p>No jobs found for this pipeline.</p>
          </div>
        ) : (
          <div className="stages-container">
            {stageNames.map((stageName) => (
              <div key={stageName} className="stage-section">
                <h4 className="stage-title">{stageName}</h4>
                <div className="jobs-grid">
                  {jobsByStage[stageName].map((job) => (
                    <div
                      key={job.id}
                      className={`job-card ${job.status}`}
                      onClick={() => handleJobClick(job)}
                      style={{ borderLeftColor: getJobStatusColor(job.status) }}
                    >
                      <div className="job-header">
                        <h5 className="job-name">{job.name}</h5>
                        <StatusBadge status={job.status} size="small" />
                      </div>
                      <div className="job-details">
                        <p><strong>Stage:</strong> {job.stage}</p>
                        {job.started_at && (
                          <p><strong>Started:</strong> {new Date(job.started_at).toLocaleString()}</p>
                        )}
                        {job.finished_at && (
                          <p><strong>Finished:</strong> {new Date(job.finished_at).toLocaleString()}</p>
                        )}
                      </div>
                      <div className="job-actions">
                        <span className="view-logs-hint">Click to view logs</span>
                        {job.web_url && (
                          <a 
                            href={job.web_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="external-link"
                            onClick={(e) => e.stopPropagation()}
                          >
                            GitLab 🔗
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};