import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { WorkflowStepper } from './WorkflowStepper';
import { WorkflowControls } from './WorkflowControls';
import { ProjectInfo } from './ProjectInfo';
import { useWorkflow } from '../../hooks/useWorkflow';
import { usePolling } from '../../hooks/usePolling';
import { LoadingSpinner } from '../common/LoadingSpinner';
import './WorkflowDashboard.css';
export const WorkflowDashboard: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const {
    workflowStatus,
    startWorkflow,
    stopWorkflow,
    isLoading,
    error,
    currentSession,
    logs
  } = useWorkflow(sessionId);
  const { shouldStopPolling, stopReason } = usePolling();
  const handleStartWorkflow = async (config: any) => {
    try {
      const response = await startWorkflow(config);
      if (response.session_id) {
        navigate(`/workflow/${response.session_id}`);
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
    if (sessionId) {
      return `Workflow Session: ${sessionId}`;
    }
    return 'LLM Auto Codefix Dashboard';
  };
  const getCurrentSessionId = () => {
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
  // 检测是否存在严重错误（如GitHub HTTP错误）
  const hasFatalError = error && (
    error.toLowerCase().includes('fatal:') || 
    error.toLowerCase().includes('unencrypted http') ||
    error.toLowerCase().includes('authentication failed') ||
    error.toLowerCase().includes('permission denied')
  );
  return (
    <div className="workflow-dashboard">
      <div className="dashboard-header">
        <h1>{getDisplayTitle()}</h1>
        {displaySessionId && (
          <p className="session-info">
            Session ID: <code>{displaySessionId}</code>
          </p>
        )}
      </div>
      {/* 显示致命错误消息 */}
      {hasFatalError && (
        <div className="fatal-error-message">
          <h3>Fatal Error</h3>
          <p>{error}</p>
          <div className="error-actions">
            <button onClick={() => window.location.reload()} className="btn btn-primary">
              Restart
            </button>
            <a href="https://docs.github.com/en/get-started/getting-started-with-git/about-remote-repositories#https-vs-ssh-urls" 
               target="_blank" rel="noopener noreferrer" 
               className="btn btn-secondary">
              Documentation
            </a>
          </div>
          {error.toLowerCase().includes('unencrypted http') && (
            <div className="error-help">
              <h4>Troubleshooting</h4>
              <p>GitHub requires HTTPS for repository URLs. Please ensure:</p>
              <ul>
                <li>Your repository URL uses HTTPS instead of HTTP</li>
                <li>Your Git configuration is set up correctly</li>
                <li>You have proper authentication credentials configured</li>
              </ul>
            </div>
          )}
        </div>
      )}
      {/* 显示普通错误消息 */}
      {error && !hasFatalError && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="btn btn-primary">
            Retry
          </button>
        </div>
      )}
      {/* 显示停止轮询的原因 */}
      {shouldStopPolling && stopReason && !error && (
        <div className="polling-stopped-message">
          <h3>Monitoring Stopped</h3>
          <p>{stopReason}</p>
        </div>
      )}
      <div className="dashboard-content">
        {/* 左侧操作区 */}
        <div className="left-panel">
          <div className="panel-section">
            <WorkflowControls
              onStart={handleStartWorkflow}
              onStop={handleStopWorkflow}
              isRunning={workflowStatus?.status === 'running'}
              disabled={isLoading || hasFatalError}
              workflowStatus={workflowStatus}
            />
          </div>
          <div className="panel-section">
            <ProjectInfo
              workflowStatus={workflowStatus}
              onViewPipeline={(projectName) => {
                const projName = projectName.replace('/', '-');
                navigate(`/${projName}/pipeline`);
              }}
            />
          </div>
        </div>
        {/* 右侧状态区 */}
        <div className="right-panel">
          <div className="panel-section">
            <WorkflowStepper
              steps={workflowStatus?.steps}
              currentStep={workflowStatus?.current_step}
              status={workflowStatus?.status}
              shouldStopPolling={shouldStopPolling}
              stepErrors={
                error ? { [workflowStatus?.current_step || 'prepare_project']: error } : {}
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
};