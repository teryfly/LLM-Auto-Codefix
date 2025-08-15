import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { WorkflowStepper } from './WorkflowStepper';
import { WorkflowControls } from './WorkflowControls';
import { ProjectInfo } from './ProjectInfo';
import { useWorkflow } from '../../hooks/useWorkflow';
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
    currentSession
  } = useWorkflow(sessionId);
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
      {error && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="btn btn-primary">
            Retry
          </button>
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
              disabled={isLoading}
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
            />
          </div>
        </div>
      </div>
    </div>
  );
};