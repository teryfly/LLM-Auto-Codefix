import { useState, useEffect, useCallback } from 'react';
import { workflowApi } from '../services/workflow-api';
import { usePolling } from './usePolling';
interface WorkflowStep {
  name: string;
  display_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  description?: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}
interface WorkflowStatus {
  session_id: string;
  status: string;
  current_step: string;
  steps: Record<string, WorkflowStep>;
  project_info?: {
    project_name?: string;
    project_id?: number;
  };
  pipeline_info?: {
    pipeline_id?: number;
    merge_request?: {
      id?: number;
      iid?: number;
      web_url?: string;
      title?: string;
    };
  };
  error_message?: string;
  started_at?: string;
  updated_at?: string;
}
export const useMRWorkflow = (projectName?: string, mrId?: string) => {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRecovered, setIsRecovered] = useState(false);
  const { isPolling } = usePolling();
  const fetchWorkflowStatusByMR = useCallback(async (projName: string, mrIdValue: string) => {
    try {
      setIsLoading(true);
      const status = await workflowApi.getWorkflowStatusByMR(projName, mrIdValue);
      setWorkflowStatus(status);
      setIsRecovered(status.status === 'recovered');
      setError(null);
      // 如果是恢复的状态，需要持续轮询以更新实时状态
      if (status.status === 'recovered') {
        await updateRecoveredWorkflowStatus(status);
      }
    } catch (err) {
      console.error('Failed to fetch workflow status by MR:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch workflow status');
    } finally {
      setIsLoading(false);
    }
  }, []);
  const updateRecoveredWorkflowStatus = async (currentStatus: WorkflowStatus) => {
    if (!projectName || !mrId) return;
    try {
      // 按步骤顺序检查状态
      const stepOrder = [
        'prepare_project',
        'create_mr', 
        'debug_loop',
        'merge_mr',
        'post_merge_monitor'
      ];
      const updatedSteps = { ...currentStatus.steps };
      let currentStepIndex = 0;
      let allCompleted = true;
      // 找到当前正在执行的步骤
      for (let i = 0; i < stepOrder.length; i++) {
        const stepName = stepOrder[i];
        const step = updatedSteps[stepName];
        if (step.status === 'pending') {
          currentStepIndex = i;
          allCompleted = false;
          break;
        } else if (step.status === 'running') {
          currentStepIndex = i;
          allCompleted = false;
          break;
        } else if (step.status === 'failed') {
          currentStepIndex = i;
          allCompleted = false;
          break;
        }
      }
      // 如果所有步骤都完成了
      if (allCompleted) {
        setWorkflowStatus({
          ...currentStatus,
          status: 'completed',
          current_step: 'post_merge_monitor',
          steps: updatedSteps
        });
        return;
      }
      // 模拟步骤进度检查（这里应该调用实际的API来检查GitLab状态）
      const currentStepName = stepOrder[currentStepIndex];
      const isStepCompleted = await checkStepStatus(projectName, mrId, currentStepName);
      if (isStepCompleted) {
        updatedSteps[currentStepName].status = 'completed';
        updatedSteps[currentStepName].completed_at = new Date().toISOString();
        // 如果不是最后一个步骤，开始下一个步骤
        if (currentStepIndex < stepOrder.length - 1) {
          const nextStepName = stepOrder[currentStepIndex + 1];
          updatedSteps[nextStepName].status = 'running';
          updatedSteps[nextStepName].started_at = new Date().toISOString();
        }
      } else {
        // 步骤仍在进行中
        updatedSteps[currentStepName].status = 'running';
        if (!updatedSteps[currentStepName].started_at) {
          updatedSteps[currentStepName].started_at = new Date().toISOString();
        }
      }
      setWorkflowStatus({
        ...currentStatus,
        status: allCompleted ? 'completed' : 'running',
        current_step: currentStepName,
        steps: updatedSteps,
        updated_at: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error updating recovered workflow status:', error);
    }
  };
  const checkStepStatus = async (projName: string, mrIdValue: string, stepName: string): Promise<boolean> => {
    // 这里应该实现具体的步骤状态检查逻辑
    // 目前返回一个模拟的结果
    try {
      switch (stepName) {
        case 'prepare_project':
          // 检查项目是否存在
          return true; // 假设项目总是存在的
        case 'create_mr':
          // 检查MR是否创建
          return true; // 如果能通过MR ID访问，说明MR已创建
        case 'debug_loop':
          // 检查pipeline状态
          // 这里需要调用GitLab API检查pipeline状态
          return Math.random() > 0.5; // 模拟随机完成
        case 'merge_mr':
          // 检查MR是否已合并
          return Math.random() > 0.7; // 模拟随机完成
        case 'post_merge_monitor':
          // 检查部署状态
          return Math.random() > 0.8; // 模拟随机完成
        default:
          return false;
      }
    } catch (error) {
      console.error(`Error checking step ${stepName}:`, error);
      return false;
    }
  };
  // 轮询更新状态
  useEffect(() => {
    if (projectName && mrId && isPolling && isRecovered) {
      const interval = setInterval(() => {
        if (workflowStatus) {
          updateRecoveredWorkflowStatus(workflowStatus);
        }
      }, 5000); // 每5秒更新一次
      return () => clearInterval(interval);
    }
  }, [projectName, mrId, isPolling, isRecovered, workflowStatus]);
  // 初始加载
  useEffect(() => {
    if (projectName && mrId) {
      fetchWorkflowStatusByMR(projectName, mrId);
    }
  }, [projectName, mrId, fetchWorkflowStatusByMR]);
  return {
    workflowStatus,
    isLoading,
    error,
    isRecovered,
    refreshStatus: () => {
      if (projectName && mrId) {
        fetchWorkflowStatusByMR(projectName, mrId);
      }
    }
  };
};