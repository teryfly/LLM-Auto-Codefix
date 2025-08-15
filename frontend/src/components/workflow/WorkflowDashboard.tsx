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
  if (isLoading && !workflowStatus) {
    return (
      <div className="dashboard-loading">
        <LoadingSpinner />
        <p>Loading workflow dashboard...</p>
      </div>
    );
  }
  const displaySessionId = getCurrentSessionId();
  return (
    <div className="workflow-dashboard">
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
              {isRecovered && (
                <p className="recovery-info">
                  <span className="recovery-badge">🔄 Status Recovered</span>
                  Workflow status recovered from GitLab MR information
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
            disabled={!pipelineStatus}
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
            <button onClick={refreshStatus} className="btn btn-secondary btn-small">
              🔄 Retry Recovery
            </button>
          )}
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
                />
              </div>
            )}
            <div className="workflow-section">
              <WorkflowStepper
                steps={workflowStatus?.steps}
                currentStep={workflowStatus?.current_step}
                status={workflowStatus?.status}
                isRecovered={isRecovered}
              />
            </div>
            <div className="workflow-section">
              <WorkflowStatus
                status={workflowStatus}
                pipelineStatus={pipelineStatus}
                isRecovered={isRecovered}
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