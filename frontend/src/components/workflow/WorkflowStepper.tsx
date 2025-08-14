import React from 'react';
import { StatusBadge } from '../common/StatusBadge';
import './WorkflowStepper.css';
interface WorkflowStep {
  name: string;
  display_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  description?: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}
interface WorkflowStepperProps {
  steps?: Record<string, WorkflowStep>;  // 添加可选标记
  currentStep?: string;                  // 添加可选标记
  status?: string;                       // 添加可选标记
}
export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({
  steps = {},      // 提供默认值
  currentStep = '',
  status = 'unknown'
}) => {
  const stepOrder = [
    'prepare_project',
    'create_mr',
    'debug_loop',
    'merge_mr',
    'post_merge_monitor'
  ];
  // 如果 steps 为空，创建默认的步骤结构
  const defaultSteps: Record<string, WorkflowStep> = {
    prepare_project: {
      name: 'prepare_project',
      display_name: '准备项目',
      status: 'pending',
      description: '项目准备和代码同步'
    },
    create_mr: {
      name: 'create_mr',
      display_name: '创建合并请求',
      status: 'pending',
      description: '创建MR并触发Pipeline'
    },
    debug_loop: {
      name: 'debug_loop',
      display_name: '调试循环',
      status: 'pending',
      description: '监控Pipeline并执行LLM修复'
    },
    merge_mr: {
      name: 'merge_mr',
      display_name: '合并部署',
      status: 'pending',
      description: '合并MR并等待部署Pipeline'
    },
    post_merge_monitor: {
      name: 'post_merge_monitor',
      display_name: '部署监控',
      status: 'pending',
      description: '监控合并后的部署状态'
    }
  };
  // 使用传入的 steps 或默认 steps
  const workflowSteps = Object.keys(steps).length > 0 ? steps : defaultSteps;
  const getStepIcon = (stepStatus: string, isActive: boolean) => {
    switch (stepStatus) {
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      case 'running':
        return '🔄';
      case 'skipped':
        return '⏭️';
      default:
        return isActive ? '🔵' : '⚪';
    }
  };
  const getStepClass = (step: WorkflowStep, stepName: string) => {
    const isActive = stepName === currentStep;
    const isCompleted = step.status === 'completed';
    const isFailed = step.status === 'failed';
    const isRunning = step.status === 'running';
    return [
      'workflow-step',
      isActive && 'active',
      isCompleted && 'completed',
      isFailed && 'failed',
      isRunning && 'running'
    ].filter(Boolean).join(' ');
  };
  return (
    <div className="workflow-stepper">
      <div className="stepper-header">
        <h3>Workflow Progress</h3>
        <StatusBadge status={status} />
      </div>
      <div className="stepper-content">
        <div className="steps-container">
          {stepOrder.map((stepName, index) => {
            const step = workflowSteps[stepName];
            // 如果步骤不存在，跳过
            if (!step) {
              console.warn(`Step ${stepName} not found in workflow steps`);
              return null;
            }
            const isActive = stepName === currentStep;
            const isLast = index === stepOrder.length - 1;
            return (
              <div key={stepName} className="step-wrapper">
                <div className={getStepClass(step, stepName)}>
                  <div className="step-indicator">
                    <div className="step-icon">
                      {getStepIcon(step.status, isActive)}
                    </div>
                    <div className="step-number">{index + 1}</div>
                  </div>
                  <div className="step-content">
                    <div className="step-header">
                      <h4 className="step-title">{step.display_name}</h4>
                      <StatusBadge status={step.status} size="small" />
                    </div>
                    {step.description && (
                      <p className="step-description">{step.description}</p>
                    )}
                    {step.error_message && (
                      <div className="step-error">
                        <span className="error-icon">⚠️</span>
                        <span className="error-text">{step.error_message}</span>
                      </div>
                    )}
                    <div className="step-timing">
                      {step.started_at && (
                        <span className="timing-info">
                          Started: {new Date(step.started_at).toLocaleTimeString()}
                        </span>
                      )}
                      {step.completed_at && (
                        <span className="timing-info">
                          Completed: {new Date(step.completed_at).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                {!isLast && (
                  <div className={`step-connector ${step.status === 'completed' ? 'completed' : ''}`}>
                    <div className="connector-line"></div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};