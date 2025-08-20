import React from 'react';
import './WorkflowProgressBar.css';
interface WorkflowStep {
  name: string;
  display_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
}
interface WorkflowProgressBarProps {
  steps?: Record<string, WorkflowStep>;
  currentStep?: string;
  status?: string;
}
export const WorkflowProgressBar: React.FC<WorkflowProgressBarProps> = ({
  steps = {},
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
  const stepDisplayNames: Record<string, string> = {
    prepare_project: '项目准备',
    create_mr: '创建MR',
    debug_loop: '调试循环',
    merge_mr: '合并部署',
    post_merge_monitor: '部署监控'
  };
  const getStepStatus = (stepName: string) => {
    if (steps[stepName]) {
      return steps[stepName].status;
    }
    // 如果没有步骤信息，根据当前步骤推断状态
    const currentIndex = stepOrder.indexOf(currentStep);
    const stepIndex = stepOrder.indexOf(stepName);
    if (stepIndex < currentIndex) {
      return 'completed';
    } else if (stepIndex === currentIndex) {
      return status === 'failed' ? 'failed' : 'running';
    } else {
      return 'pending';
    }
  };
  const getStepIcon = (stepStatus: string) => {
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
        return '⚪';
    }
  };
  return (
    <div className="workflow-progress-bar">
      <div className="progress-steps">
        {stepOrder.map((stepName, index) => {
          const stepStatus = getStepStatus(stepName);
          const isActive = stepName === currentStep;
          const isLast = index === stepOrder.length - 1;
          return (
            <div key={stepName} className="progress-step-wrapper">
              <div className={`progress-step ${stepStatus} ${isActive ? 'active' : ''}`}>
                <div className="step-icon">
                  {getStepIcon(stepStatus)}
                </div>
                <div className="step-info">
                  <div className="step-name">
                    {stepDisplayNames[stepName] || stepName}
                  </div>
                  <div className="step-status-text">
                    {stepStatus === 'running' ? '进行中' : 
                     stepStatus === 'completed' ? '已完成' :
                     stepStatus === 'failed' ? '失败' :
                     stepStatus === 'skipped' ? '跳过' : '等待中'}
                  </div>
                </div>
              </div>
              {!isLast && (
                <div className={`step-connector ${stepStatus === 'completed' ? 'completed' : ''}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};