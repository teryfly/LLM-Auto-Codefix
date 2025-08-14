import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { WorkflowStepper } from './WorkflowStepper';
import { WorkflowControls } from './WorkflowControls';
import { WorkflowStatus } from './WorkflowStatus';
import { PipelineMonitor } from '../pipeline/PipelineMonitor';
import { LogViewer } from '../pipeline/LogViewer';
import { useWorkflow } from '../../hooks/useWorkflow';
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
  const {
    workflowStatus,
    startWorkflow,
    stopWorkflow,
    isLoading: workflowLoading,
    error: workflowError,
    currentSession
  } = useWorkflow(sessionId);
  const {
    pipelineStatus,
    jobStatuses,
    isLoading: pipelineLoading
  } = usePipeline(sessionId);
  // 如果是MR路由，尝试从MR信息获取session
  useEffect(() => {
    if (projectName && mrId && !sessionId) {
      // 这里可以添加逻辑通过MR ID查找对应的session
      // 暂时显示MR信息
      console.log(`Viewing MR ${mrId} for project ${projectName}`);
    }
  }, [projectName, mrId, sessionId]);
  const handleStartWorkflow = async (config: any) => {
    try {
      const response = await startWorkflow(config);
      // 获取项目信息和MR信息，跳转到MR路由
      if (response.session_id && config.project_name) {
        // 等待一段时间让workflow创建MR
        setTimeout(async () => {
          try {
            // 这里需要从workflow状态中获取MR ID
            // 暂时使用session ID作为占位符
            const projectNameForUrl = config.project_name.replace('/', '-');
            navigate(`/${projectNameForUrl}/MR/${response.session_id}`);
          } catch (error) {
            console.error('Failed to navigate to MR route:', error);
          }
        }, 5000);
      }
    } catch (error) {
      console.error('Failed to start workflow:', error);
    }
  };
  const handleStopWorkflow = async () => {
    if (sessionId || currentSession) {
      try {
        await stopWorkflow(sessionId || currentSession);
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
    return sessionId || currentSession || (projectName && mrId ? mrId : null);
  };
  if (workflowLoading && !workflowStatus) {
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
            <p className="mr-info">
              MR ID: <code>{mrId}</code> | Project: <code>{projectName.replace('-', '/')}</code>
            </p>
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
        </div>
      )}
      <div className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="workflow-section">
              <WorkflowControls
                onStart={handleStartWorkflow}
                onStop={handleStopWorkflow}
                isRunning={workflowStatus?.status === 'running'}
                disabled={workflowLoading}
              />
            </div>
            <div className="workflow-section">
              <WorkflowStepper
                steps={workflowStatus?.steps}
                currentStep={workflowStatus?.current_step}
                status={workflowStatus?.status}
              />
            </div>
            <div className="workflow-section">
              <WorkflowStatus
                status={workflowStatus}
                pipelineStatus={pipelineStatus}
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