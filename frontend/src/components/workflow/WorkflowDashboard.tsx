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
  const {
    pipelineStatus,
    jobStatuses,
    isLoading: pipelineLoading
  } = usePipeline(sessionId || (isMRRoute ? `mr-${projectName}-${mrId}` : undefined));
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
    if (isRecovered) {
      return 'Status recovered from GitLab MR information';
    }
    return null;
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
                <p className={`status-message ${mrExists === false ? 'error-info' : isRecovered ? 'recovery-info' : shouldStopPolling ? 'completion-info' : ''}`}>
                  <span className={`status-badge ${mrExists === false ? 'error-badge' : isRecovered ? 'recovery-badge' : shouldStopPolling ? 'completion-badge' : ''}`}>
                    {mrExists === false ? '❌ Not Found' : 
                     shouldStopPolling && workflowStatus?.status === 'completed' ? '✅ Completed' :
                     shouldStopPolling && workflowStatus?.status === 'failed' ? '❌ Failed' :
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
            disabled={!pipelineStatus && !isMRRoute}
          >
            Pipeline
          </button>
          <button
            className={`tab-button ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
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
      {shouldStopPolling && (
        <div className={`polling-status ${workflowStatus?.status === 'completed' ? 'success' : 'warning'}`}>
          <div className="polling-status-content">
            <span className="polling-icon">
              {workflowStatus?.status === 'completed' ? '✅' : '⏹️'}
            </span>
            <span className="polling-text">
              {workflowStatus?.status === 'completed' ? 
                'Workflow completed - automatic status updates stopped' :
                'Status polling stopped due to error or completion'
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
                shouldStopPolling={shouldStopPolling}
              />
            </div>
            <div className="workflow-section">
              <WorkflowStatus
                status={workflowStatus}
                pipelineStatus={pipelineStatus}
                isRecovered={isRecovered}
                mrExists={mrExists}
                shouldStopPolling={shouldStopPolling}
              />
            </div>
          </div>
        )}
        {activeTab === 'pipeline' && displaySessionId && (
          <div className="pipeline-tab">
            <PipelineMonitor sessionId={displaySessionId} />
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