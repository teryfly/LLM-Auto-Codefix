import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { WorkflowStepper } from './WorkflowStepper';
import { WorkflowControls } from './WorkflowControls';
import { WorkflowStatus } from './WorkflowStatus';
import { PipelineMonitor } from '../pipeline/PipelineMonitor';
import { LogViewer } from '../pipeline/LogViewer';
import { useWorkflow } from '../../hooks/useWorkflow';
import { useMRWorkflow } from '../../hooks/useMRWorkflow';
import { usePipeline } from '../../hooks/usePipeline';
import { LoadingSpinner } from '../common/LoadingSpinner';
import './WorkflowDashboard.css';
export const WorkflowDashboard: React.FC = () => {
  const { sessionId, projectName, mrId } = useParams<{ 
    sessionId: string; 
    projectName: string; 
    mrId: string; 
  }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'pipeline' | 'logs'>('overview');
  // 根据路由类型选择不同的hook
  const isMRRoute = projectName && mrId;
  // 普通workflow hook
  const {
    workflowStatus: normalWorkflowStatus,
    startWorkflow,
    stopWorkflow,
    isLoading: normalWorkflowLoading,
    error: normalWorkflowError,
    currentSession
  } = useWorkflow(isMRRoute ? undefined : sessionId);
  // MR恢复workflow hook
  const {
    workflowStatus: mrWorkflowStatus,
    ciStatus,
    isLoading: mrWorkflowLoading,
    error: mrWorkflowError,
    isRecovered,
    stepErrors,
    shouldStopPolling,
    mrExists,
    refreshStatus
  } = useMRWorkflow(isMRRoute ? projectName : undefined, isMRRoute ? mrId : undefined);
  // 选择使用哪个状态
  const workflowStatus = isMRRoute ? mrWorkflowStatus : normalWorkflowStatus;
  const isLoading = isMRRoute ? mrWorkflowLoading : normalWorkflowLoading;
  const workflowError = isMRRoute ? mrWorkflowError : normalWorkflowError;
  // 为Pipeline监控确定session ID
  const pipelineSessionId = sessionId || (isMRRoute ? `mr-${projectName}-${mrId}` : undefined);
  const {
    pipelineStatus,
    jobStatuses,
    isLoading: pipelineLoading
  } = usePipeline(pipelineSessionId);
  // 遇到错误时停止轮询
  useEffect(() => {
    if (workflowError && isMRRoute) {
      console.log('Error detected, stopping polling');
      // 通过刷新状态来停止轮询
      if (refreshStatus) {
        // 设置一个标志来停止轮询，而不是继续刷新
        // 这里我们不调用refreshStatus，让shouldStopPolling生效
      }
    }
  }, [workflowError, isMRRoute, refreshStatus]);
  const handleStartWorkflow = async (config: any) => {
    try {
      const response = await startWorkflow(config);
      // 等待workflow创建MR后跳转
      if (response.session_id && config.project_name) {
        setTimeout(async () => {
          try {
            // 获取workflow状态以获取MR信息
            const status = await fetch(`/api/v1/workflow/status/${response.session_id}`);
            const statusData = await status.json();
            if (statusData.pipeline_info?.merge_request?.iid) {
              const projectNameForUrl = config.project_name.replace('/', '-');
              const mrIid = statusData.pipeline_info.merge_request.iid;
              navigate(`/${projectNameForUrl}/MR/${mrIid}`);
            }
          } catch (error) {
            console.error('Failed to navigate to MR route:', error);
          }
        }, 10000); // 等待10秒让MR创建完成
      }
    } catch (error) {
      console.error('Failed to start workflow:', error);
    }
  };
  const handleStopWorkflow = async () => {
    const targetSessionId = sessionId || currentSession;
    if (targetSessionId) {
      try {
        await stopWorkflow(targetSessionId);
      } catch (error) {
        console.error('Failed to stop workflow:', error);
      }
    }
  };
  const getDisplayTitle = () => {
    if (projectName && mrId) {
      return `Project: ${projectName.replace('-', '/')} - MR: ${mrId}`;
    }
    if (sessionId) {
      return `Session: ${sessionId}`;
    }
    return 'Workflow Dashboard';
  };
  const getCurrentSessionId = () => {
    if (isMRRoute) {
      return workflowStatus?.session_id || `mr-${projectName}-${mrId}`;
    }
    return sessionId || currentSession || null;
  };
  const getStatusMessage = () => {
    if (isMRRoute && mrExists === false) {
      return `MR ${mrId} not found in project ${projectName?.replace('-', '/')}`;
    }
    if (shouldStopPolling && workflowStatus?.status === 'completed') {
      return 'Workflow completed successfully';
    }
    if (shouldStopPolling && workflowStatus?.status === 'failed') {
      return 'Workflow failed - polling stopped';
    }
    if (workflowError) {
      return 'Error occurred - polling stopped';
    }
    if (isRecovered) {
      return 'Status recovered from GitLab MR information';
    }
    return null;
  };
  // 检查是否有Pipeline数据可显示
  const hasPipelineData = () => {
    if (isMRRoute && ciStatus) {
      return ciStatus.pipeline || ciStatus.jobs.length > 0;
    }
    return pipelineStatus || jobStatuses.length > 0;
  };
  if (isLoading && !workflowStatus) {
    return (
      <div className="dashboard-loading">
        <LoadingSpinner />
        <p>
          {isMRRoute ? 
            `Validating MR ${mrId} and loading workflow status...` : 
            'Loading workflow dashboard...'
          }
        </p>
      </div>
    );
  }
  const displaySessionId = getCurrentSessionId();
  const statusMessage = getStatusMessage();
  return (
    <div className={`workflow-dashboard ${isMRRoute ? 'mr-route-dashboard' : ''} ${mrExists === false ? 'error-state' : ''}`}>
      <div className="dashboard-header">
        <div className="dashboard-title">
          <h2>{getDisplayTitle()}</h2>
          {displaySessionId && (
            <p className="session-info">
              Session: <code>{displaySessionId}</code>
            </p>
          )}
          {projectName && mrId && (
            <div className="mr-route-info">
              <p className="mr-info">
                MR ID: <code>{mrId}</code> | Project: <code>{projectName.replace('-', '/')}</code>
              </p>
              {statusMessage && (
                <p className={`status-message ${mrExists === false ? 'error-info' : isRecovered ? 'recovery-info' : shouldStopPolling || workflowError ? 'completion-info' : ''}`}>
                  <span className={`status-badge ${mrExists === false ? 'error-badge' : 
                     shouldStopPolling && workflowStatus?.status === 'completed' ? 'completion-badge' :
                     shouldStopPolling && workflowStatus?.status === 'failed' ? 'error-badge' :
                     workflowError ? 'error-badge' :
                     isRecovered ? 'recovery-badge' : ''}`}>
                    {mrExists === false ? '❌ Not Found' : 
                     shouldStopPolling && workflowStatus?.status === 'completed' ? '✅ Completed' :
                     shouldStopPolling && workflowStatus?.status === 'failed' ? '❌ Failed' :
                     workflowError ? '❌ Error' :
                     isRecovered ? '🔄 Recovered' : ''}
                  </span>
                  {statusMessage}
                </p>
              )}
            </div>
          )}
        </div>
        <div className="dashboard-tabs">
          <button
            className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab-button ${activeTab === 'pipeline' ? 'active' : ''}`}
            onClick={() => setActiveTab('pipeline')}
            disabled={!hasPipelineData()}
          >
            Pipeline
          </button>
          <button
            className={`tab-button ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
            disabled={!displaySessionId}
          >
            Logs
          </button>
        </div>
      </div>
      {workflowError && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{workflowError}</p>
          {isMRRoute && (
            <div className="error-actions">
              <button onClick={refreshStatus} className="btn btn-secondary btn-small">
                🔄 Retry Validation
              </button>
              {mrExists === false && (
                <p className="error-suggestion">
                  Please check if the MR ID <strong>{mrId}</strong> exists in project <strong>{projectName?.replace('-', '/')}</strong>.
                  You can verify this in GitLab directly.
                </p>
              )}
            </div>
          )}
        </div>
      )}
      {(shouldStopPolling || workflowError) && (
        <div className={`polling-status ${workflowStatus?.status === 'completed' ? 'success' : 'warning'}`}>
          <div className="polling-status-content">
            <span className="polling-icon">
              {workflowStatus?.status === 'completed' ? '✅' : workflowError ? '❌' : '⏹️'}
            </span>
            <span className="polling-text">
              {workflowError ? 
                'Error occurred - automatic status updates stopped' :
                workflowStatus?.status === 'completed' ? 
                'Workflow completed - automatic status updates stopped' :
                'Status polling stopped due to completion or error'
              }
            </span>
            {isMRRoute && (
              <button onClick={refreshStatus} className="btn btn-secondary btn-small">
                🔄 Resume Monitoring
              </button>
            )}
          </div>
        </div>
      )}
      <div className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            {!isMRRoute && (
              <div className="workflow-section">
                <WorkflowControls
                  onStart={handleStartWorkflow}
                  onStop={handleStopWorkflow}
                  isRunning={workflowStatus?.status === 'running'}
                  disabled={isLoading}
                  workflowStatus={workflowStatus}
                />
              </div>
            )}
            <div className={`workflow-section ${mrExists === false ? 'error-state' : ''}`}>
              <WorkflowStepper
                steps={workflowStatus?.steps}
                currentStep={workflowStatus?.current_step}
                status={workflowStatus?.status}
                isRecovered={isRecovered}
                stepErrors={stepErrors}
                mrExists={mrExists}
                shouldStopPolling={shouldStopPolling || !!workflowError}
              />
            </div>
            <div className="workflow-section">
              <WorkflowStatus
                status={workflowStatus}
                pipelineStatus={pipelineStatus}
                ciStatus={ciStatus}
                isRecovered={isRecovered}
                mrExists={mrExists}
                shouldStopPolling={shouldStopPolling || !!workflowError}
              />
            </div>
          </div>
        )}
        {activeTab === 'pipeline' && hasPipelineData() && (
          <div className="pipeline-tab">
            {isMRRoute && ciStatus ? (
              <div className="mr-pipeline-monitor">
                <h3>CI/CD Pipeline Status</h3>
                {ciStatus.pipeline && (
                  <div className="pipeline-info">
                    <p><strong>Pipeline ID:</strong> {ciStatus.pipeline.id}</p>
                    <p><strong>Status:</strong> {ciStatus.pipeline.status}</p>
                    <p><strong>Branch:</strong> {ciStatus.pipeline.ref}</p>
                    {ciStatus.pipeline.web_url && (
                      <p><strong>GitLab URL:</strong> 
                        <a href={ciStatus.pipeline.web_url} target="_blank" rel="noopener noreferrer">
                          View in GitLab 🔗
                        </a>
                      </p>
                    )}
                  </div>
                )}
                {ciStatus.jobs.length > 0 && (
                  <div className="jobs-list">
                    <h4>Jobs ({ciStatus.jobs.length})</h4>
                    <div className="jobs-grid">
                      {ciStatus.jobs.map((job) => (
                        <div key={job.id} className={`job-card ${job.status}`}>
                          <h5>{job.name}</h5>
                          <p><strong>Stage:</strong> {job.stage}</p>
                          <p><strong>Status:</strong> {job.status}</p>
                          {job.started_at && (
                            <p><strong>Started:</strong> {new Date(job.started_at).toLocaleString()}</p>
                          )}
                          {job.finished_at && (
                            <p><strong>Finished:</strong> {new Date(job.finished_at).toLocaleString()}</p>
                          )}
                          {job.web_url && (
                            <a href={job.web_url} target="_blank" rel="noopener noreferrer">
                              View Job 🔗
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <PipelineMonitor sessionId={displaySessionId!} />
            )}
          </div>
        )}
        {activeTab === 'logs' && displaySessionId && (
          <div className="logs-tab">
            <LogViewer sessionId={displaySessionId} />
          </div>
        )}
      </div>
    </div>
  );
};