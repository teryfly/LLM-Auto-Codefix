import { useState, useEffect, useCallback, useRef } from 'react';
import { workflowApi } from '../services/workflow-api';
import { gitlabApi } from '../services/gitlab-api';
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
interface CIStatus {
  merge_request: {
    id: number;
    iid: number;
    title: string;
    state: string;
    source_branch: string;
    target_branch: string;
    web_url: string;
  };
  pipeline?: {
    id: number;
    status: string;
    ref: string;
    web_url: string;
    created_at?: string;
    updated_at?: string;
  };
  jobs: Array<{
    id: number;
    name: string;
    status: string;
    stage: string;
    started_at?: string;
    finished_at?: string;
    web_url?: string;
  }>;
  overall_status: string;
}
export const useMRWorkflow = (projectName?: string, mrId?: string) => {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [ciStatus, setCiStatus] = useState<CIStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRecovered, setIsRecovered] = useState(false);
  const [stepErrors, setStepErrors] = useState<Record<string, string>>({});
  const [shouldStopPolling, setShouldStopPolling] = useState(false);
  const [mrExists, setMrExists] = useState<boolean | null>(null);
  const { isPolling } = usePolling();
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  // 验证MR是否存在并获取CI状态
  const validateMRAndGetCIStatus = useCallback(async (projName: string, mrIdValue: string): Promise<boolean> => {
    try {
      const ciStatusData = await gitlabApi.getMergeRequestCIStatus(projName, mrIdValue);
      setCiStatus(ciStatusData);
      return true;
    } catch (error) {
      console.error(`MR ${mrIdValue} validation failed:`, error);
      setCiStatus(null);
      return false;
    }
  }, []);
  const fetchWorkflowStatusByMR = useCallback(async (projName: string, mrIdValue: string) => {
    try {
      setIsLoading(true);
      setError(null);
      setShouldStopPolling(false);
      // 首先验证MR是否存在并获取CI状态
      console.log(`Validating MR ${mrIdValue} in project ${projName} and fetching CI status...`);
      const mrExistsResult = await validateMRAndGetCIStatus(projName, mrIdValue);
      setMrExists(mrExistsResult);
      if (!mrExistsResult) {
        // MR不存在，立即创建错误状态并停止
        const errorStatus = createNotFoundStatus(projName, mrIdValue);
        setWorkflowStatus(errorStatus);
        setIsRecovered(false);
        setShouldStopPolling(true);
        setError(`Merge Request ${mrIdValue} not found in project ${projName}`);
        return;
      }
      // MR存在，尝试获取workflow状态
      console.log(`MR ${mrIdValue} exists, fetching workflow status...`);
      try {
        const status = await workflowApi.getWorkflowStatusByMR(projName, mrIdValue);
        setWorkflowStatus(status);
        setIsRecovered(status.status === 'recovered');
        // 检查是否应该停止轮询
        if (status.status === 'completed' || status.status === 'failed') {
          setShouldStopPolling(true);
          console.log(`Workflow status is ${status.status}, stopping polling`);
        }
      } catch (workflowError) {
        // 如果没有找到workflow状态，基于CI状态创建一个恢复的状态
        console.log(`No existing workflow found, creating recovered status based on CI status`);
        const recoveredStatus = createRecoveredStatusFromCI(projName, mrIdValue, ciStatus);
        setWorkflowStatus(recoveredStatus);
        setIsRecovered(true);
      }
      // 如果是恢复的状态，需要持续轮询以更新实时状态
      if (isRecovered && !shouldStopPolling) {
        await updateRecoveredWorkflowStatus(workflowStatus || createRecoveredStatusFromCI(projName, mrIdValue, ciStatus));
      }
    } catch (err) {
      console.error('Failed to fetch workflow status by MR:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch workflow status';
      setError(errorMessage);
      setShouldStopPolling(true); // 遇到任何错误都停止轮询
      // 如果是404错误，说明MR不存在
      if (errorMessage.includes('404') || errorMessage.includes('not found')) {
        setWorkflowStatus(createNotFoundStatus(projName, mrIdValue));
        setIsRecovered(false);
        setMrExists(false);
      }
    } finally {
      setIsLoading(false);
    }
  }, [validateMRAndGetCIStatus, shouldStopPolling, isRecovered, workflowStatus, ciStatus]);
  const createRecoveredStatusFromCI = (projName: string, mrIdValue: string, ciStatusData: CIStatus | null): WorkflowStatus => {
    const steps: Record<string, WorkflowStep> = {
      prepare_project: {
        name: 'prepare_project',
        display_name: '项目准备和代码同步',
        status: 'completed',
        description: '项目准备和代码同步'
      },
      create_mr: {
        name: 'create_mr',
        display_name: '创建合并请求',
        status: 'completed',
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
    let currentStep = 'debug_loop';
    let workflowStatus = 'running';
    if (ciStatusData) {
      // 根据CI状态更新步骤状态
      if (ciStatusData.merge_request.state === 'merged') {
        steps.debug_loop.status = 'completed';
        steps.merge_mr.status = 'completed';
        currentStep = 'post_merge_monitor';
        if (ciStatusData.overall_status === 'success') {
          steps.post_merge_monitor.status = 'completed';
          workflowStatus = 'completed';
        } else if (ciStatusData.overall_status === 'running' || ciStatusData.overall_status === 'pending') {
          steps.post_merge_monitor.status = 'running';
        } else if (ciStatusData.overall_status === 'failed') {
          steps.post_merge_monitor.status = 'failed';
          workflowStatus = 'failed';
        }
      } else {
        // MR还未合并，检查当前Pipeline状态
        if (ciStatusData.overall_status === 'success') {
          steps.debug_loop.status = 'completed';
          currentStep = 'merge_mr';
        } else if (ciStatusData.overall_status === 'running' || ciStatusData.overall_status === 'pending') {
          steps.debug_loop.status = 'running';
        } else if (ciStatusData.overall_status === 'failed') {
          steps.debug_loop.status = 'running'; // 失败时继续调试循环
        }
      }
    }
    return {
      session_id: `mr-${projName.replace('/', '-')}-${mrIdValue}`,
      status: workflowStatus,
      current_step: currentStep,
      steps,
      project_info: { project_name: projName },
      pipeline_info: { 
        pipeline_id: ciStatusData?.pipeline?.id,
        merge_request: { 
          iid: parseInt(mrIdValue),
          id: ciStatusData?.merge_request.id,
          web_url: ciStatusData?.merge_request.web_url,
          title: ciStatusData?.merge_request.title
        } 
      },
      started_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  };
  const createNotFoundStatus = (projName: string, mrIdValue: string): WorkflowStatus => {
    const steps: Record<string, WorkflowStep> = {
      prepare_project: {
        name: 'prepare_project',
        display_name: '项目准备和代码同步',
        status: 'failed',
        description: '项目准备和代码同步',
        error_message: `MR ${mrIdValue} not found in project ${projName}. Please verify the MR ID and project name.`
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
    return {
      session_id: `mr-${projName.replace('/', '-')}-${mrIdValue}`,
      status: 'failed',
      current_step: 'prepare_project',
      steps,
      project_info: { project_name: projName },
      pipeline_info: { merge_request: { iid: parseInt(mrIdValue) } },
      error_message: `Merge Request ${mrIdValue} not found in project ${projName}. Please check if the MR ID is correct and the project exists.`,
      started_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  };
  const updateRecoveredWorkflowStatus = async (currentStatus: WorkflowStatus) => {
    if (!projectName || !mrId || shouldStopPolling) return;
    try {
      // 重新获取CI状态
      const updatedCiStatus = await gitlabApi.getMergeRequestCIStatus(projectName, mrId);
      setCiStatus(updatedCiStatus);
      // 基于最新CI状态更新workflow状态
      const updatedStatus = createRecoveredStatusFromCI(projectName, mrId, updatedCiStatus);
      setWorkflowStatus(updatedStatus);
      // 检查是否应该停止轮询
      if (updatedStatus.status === 'completed' || updatedStatus.status === 'failed') {
        setShouldStopPolling(true);
        console.log(`Workflow status is ${updatedStatus.status}, stopping polling`);
      }
    } catch (error) {
      console.error('Error updating recovered workflow status:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to update workflow status';
      setError(errorMessage);
      setShouldStopPolling(true); // 遇到错误立即停止轮询
    }
  };
  // 清理轮询定时器
  const clearPollingInterval = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);
  // 轮询更新状态 - 受shouldStopPolling和error状态控制
  useEffect(() => {
    clearPollingInterval(); // 清理之前的定时器
    // 如果有错误或应该停止轮询，不启动新的轮询
    if (error || shouldStopPolling) {
      console.log('Polling stopped due to error or completion');
      return;
    }
    if (projectName && mrId && isPolling && isRecovered && workflowStatus && mrExists) {
      console.log('Starting polling for workflow status updates');
      pollingIntervalRef.current = setInterval(() => {
        updateRecoveredWorkflowStatus(workflowStatus);
      }, 5000); // 每5秒更新一次
      return clearPollingInterval;
    }
  }, [projectName, mrId, isPolling, isRecovered, workflowStatus, shouldStopPolling, mrExists, error, clearPollingInterval]);
  // 初始加载
  useEffect(() => {
    if (projectName && mrId) {
      fetchWorkflowStatusByMR(projectName, mrId);
    }
  }, [projectName, mrId, fetchWorkflowStatusByMR]);
  // 组件卸载时清理定时器
  useEffect(() => {
    return clearPollingInterval;
  }, [clearPollingInterval]);
  return {
    workflowStatus,
    ciStatus,
    isLoading,
    error,
    isRecovered,
    stepErrors,
    shouldStopPolling,
    mrExists,
    refreshStatus: () => {
      if (projectName && mrId) {
        setShouldStopPolling(false);
        setMrExists(null);
        setError(null); // 清除错误状态
        fetchWorkflowStatusByMR(projectName, mrId);
      }
    }
  };
};