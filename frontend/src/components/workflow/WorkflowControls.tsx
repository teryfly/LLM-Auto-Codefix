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
    project_name: 'ai/dotnet-ai-demo',
    source_branch: 'ai',
    target_branch: 'dev',
    auto_merge: true
  });
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const handleStart = async () => {
    setIsStarting(true);
    setStartError(null);
    try {
      await onStart(config);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start workflow';
      setStartError(errorMessage);
      console.error('Workflow start failed:', error);
    } finally {
      setIsStarting(false);
    }
  };
  const handleStop = async () => {
    setIsStopping(true);
    try {
      await onStop();
    } catch (error) {
      console.error('Workflow stop failed:', error);
      // 停止失败通常不需要特殊处理，因为可能工作流已经结束
    } finally {
      setIsStopping(false);
    }
  };
  const handleConfigChange = (field: keyof WorkflowConfig, value: string | boolean) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
    // 清除之前的错误信息
    if (startError) {
      setStartError(null);
    }
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
        {/* 错误显示区域 */}
        {startError && (
          <div className="error-notice">
            <div className="notice-content">
              <span className="notice-icon">⚠️</span>
              <div className="notice-text">
                <strong>Failed to start workflow:</strong>
                <br />
                {startError}
                <div className="error-actions">
                  <p><strong>Possible solutions:</strong></p>
                  <ul>
                    <li>Check if the backend server is running</li>
                    <li>Verify network connectivity</li>
                    <li>Ensure the project name is correct</li>
                    <li>Check GitLab access permissions</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
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
                  placeholder="ai/dotnet-ai-demo"
                  disabled={disabled || isStarting}
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
                    disabled={disabled || isStarting}
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
                    disabled={disabled || isStarting}
                  />
                </div>
              </div>
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={config.auto_merge}
                    onChange={(e) => handleConfigChange('auto_merge', e.target.checked)}
                    disabled={disabled || isStarting}
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
                  Starting Workflow...
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