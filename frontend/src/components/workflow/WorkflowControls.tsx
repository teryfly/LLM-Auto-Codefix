import React, { useState } from 'react';
import { LoadingSpinner } from '../common/LoadingSpinner';
import './WorkflowControls.css';
interface WorkflowConfig {
  project_name: string;
  source_branch: string;
  target_branch: string;
  auto_merge: boolean;
}
interface WorkflowControlsProps {
  onStart: (config: WorkflowConfig) => Promise<void>;
  onStop: () => Promise<void>;
  isRunning: boolean;
  disabled: boolean;
  workflowStatus?: any;
}
export const WorkflowControls: React.FC<WorkflowControlsProps> = ({
  onStart,
  onStop,
  isRunning,
  disabled,
  workflowStatus
}) => {
  const [config, setConfig] = useState<WorkflowConfig>({
    project_name: 'ai/llm-cicd-tester',
    source_branch: 'ai',
    target_branch: 'dev',
    auto_merge: true
  });
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const handleStart = async () => {
    setIsStarting(true);
    try {
      await onStart(config);
    } finally {
      setIsStarting(false);
    }
  };
  const handleStop = async () => {
    setIsStopping(true);
    try {
      await onStop();
    } finally {
      setIsStopping(false);
    }
  };
  const handleConfigChange = (field: keyof WorkflowConfig, value: string | boolean) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };
  return (
    <div className="workflow-controls">
      <div className="controls-header">
        <h3>Workflow Controls</h3>
        {isRunning && (
          <span className="status-indicator running">
            🔄 Running
          </span>
        )}
      </div>
      <div className="controls-content">
        {!isRunning ? (
          <div className="config-section">
            <h4>Configuration</h4>
            <div className="config-form">
              <div className="form-group">
                <label htmlFor="project_name">Project Name:</label>
                <input
                  id="project_name"
                  type="text"
                  value={config.project_name}
                  onChange={(e) => handleConfigChange('project_name', e.target.value)}
                  placeholder="ai/llm-cicd-tester"
                  disabled={disabled}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="source_branch">Source Branch:</label>
                  <input
                    id="source_branch"
                    type="text"
                    value={config.source_branch}
                    onChange={(e) => handleConfigChange('source_branch', e.target.value)}
                    placeholder="ai"
                    disabled={disabled}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="target_branch">Target Branch:</label>
                  <input
                    id="target_branch"
                    type="text"
                    value={config.target_branch}
                    onChange={(e) => handleConfigChange('target_branch', e.target.value)}
                    placeholder="dev"
                    disabled={disabled}
                  />
                </div>
              </div>
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={config.auto_merge}
                    onChange={(e) => handleConfigChange('auto_merge', e.target.checked)}
                    disabled={disabled}
                  />
                  <span className="checkbox-text">Auto-merge on success</span>
                </label>
              </div>
            </div>
          </div>
        ) : (
          <div className="running-info">
            <h4>Current Configuration</h4>
            <div className="config-display">
              <div className="config-item">
                <span className="config-label">Project:</span>
                <span className="config-value">{config.project_name}</span>
              </div>
              <div className="config-item">
                <span className="config-label">Branch:</span>
                <span className="config-value">{config.source_branch} → {config.target_branch}</span>
              </div>
              <div className="config-item">
                <span className="config-label">Auto-merge:</span>
                <span className="config-value">{config.auto_merge ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>
        )}
        <div className="action-buttons">
          {!isRunning ? (
            <button
              className="btn btn-primary btn-large"
              onClick={handleStart}
              disabled={disabled || isStarting}
            >
              {isStarting ? (
                <>
                  <LoadingSpinner size="small" />
                  Starting...
                </>
              ) : (
                <>
                  <span className="btn-icon">🚀</span>
                  Start Workflow
                </>
              )}
            </button>
          ) : (
            <button
              className="btn btn-danger btn-large"
              onClick={handleStop}
              disabled={disabled || isStopping}
            >
              {isStopping ? (
                <>
                  <LoadingSpinner size="small" />
                  Stopping...
                </>
              ) : (
                <>
                  <span className="btn-icon">🛑</span>
                  Stop Workflow
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};