import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
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
  const { sessionId } = useParams<{ sessionId: string }>();
  const [activeTab, setActiveTab] = useState<'overview' | 'pipeline' | 'logs'>('overview');
  const {
    workflowStatus,
    startWorkflow,
    stopWorkflow,
    isLoading: workflowLoading,
    error: workflowError
  } = useWorkflow(sessionId);
  const {
    pipelineStatus,
    jobStatuses,
    isLoading: pipelineLoading
  } = usePipeline(sessionId);
  const handleStartWorkflow = async (config: any) => {
    try {
      await startWorkflow(config);
    } catch (error) {
      console.error('Failed to start workflow:', error);
    }
  };
  const handleStopWorkflow = async () => {
    if (sessionId) {
      try {
        await stopWorkflow(sessionId);
      } catch (error) {
        console.error('Failed to stop workflow:', error);
      }
    }
  };
  if (workflowLoading && !workflowStatus) {
    return (
      <div className="dashboard-loading">
        <LoadingSpinner />
        <p>Loading workflow dashboard...</p>
      </div>
    );
  }
  return (
    <div className="workflow-dashboard">
      <div className="dashboard-header">
        <div className="dashboard-title">
          <h2>Workflow Dashboard</h2>
          {sessionId && (
            <p className="session-info">
              Session: <code>{sessionId}</code>
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
        {activeTab === 'pipeline' && sessionId && (
          <div className="pipeline-tab">
            <PipelineMonitor sessionId={sessionId} />
          </div>
        )}
        {activeTab === 'logs' && sessionId && (
          <div className="logs-tab">
            <LogViewer sessionId={sessionId} />
          </div>
        )}
      </div>
    </div>
  );
};