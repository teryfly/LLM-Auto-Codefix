import { useState, useEffect, useCallback } from 'react';
import { workflowApi } from '../services/workflow-api';
import { usePolling } from './usePolling';
interface WorkflowStatus {
  session_id: string;
  status: string;
  current_step: string;
  steps: Record<string, any>;
  project_info?: {
    project_name?: string;
    project_id?: number;
    local_dir?: string;
  };
  pipeline_info?: {
    pipeline_id?: number;
    merge_request?: {
      id?: number;
      iid?: number;
      web_url?: string;
      title?: string;
    };
    deployment_url?: string;
  };
  error_message?: string;
  started_at?: string;
  updated_at?: string;
}
interface Session {
  id: string;
  status: string;
  workflow_status?: string;
  current_step?: string;
}
interface WorkflowStartResponse {
  session_id: string;
  status: string;
  message: string;
}
export const useWorkflow = (sessionId?: string) => {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [currentSession, setCurrentSession] = useState<string | null>(sessionId || null);
  const [activeSessions, setActiveSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mrInfo, setMrInfo] = useState<{
    mrId?: string;
    projectName?: string;
    webUrl?: string;
  } | null>(null);
  const { isPolling, handlePollingResponse, forceStopPolling, pollingConfig } = usePolling();
  const fetchWorkflowStatus = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      const status = await workflowApi.getWorkflowStatus(id);
      // 检查响应中的错误信息
      handlePollingResponse(status, 'workflow status');
      setWorkflowStatus(status);
      // 提取MR信息
      if (status.pipeline_info?.merge_request) {
        const mr = status.pipeline_info.merge_request;
        const projectName = status.project_info?.project_name?.replace('/', '-');
        setMrInfo({
          mrId: mr.iid?.toString() || mr.id?.toString(),
          projectName: projectName,
          webUrl: mr.web_url
        });
      }
      // 检查是否应该停止轮询
      if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
        forceStopPolling(`Workflow ${status.status}`);
      }
      // 检查步骤错误信息
      if (status.steps) {
        for (const [stepName, stepData] of Object.entries(status.steps)) {
          if (stepData.status === 'failed' && stepData.error_message) {
            // 如果是合并步骤失败，立即停止轮询
            if (stepName === 'merge_mr' && stepData.error_message.includes('conflicts')) {
              forceStopPolling(`Merge step failed: ${stepData.error_message}`);
              break;
            }
          }
        }
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch workflow status:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch workflow status';
      setError(errorMessage);
      // 检查错误并停止轮询
      handlePollingResponse({ error: errorMessage }, 'workflow API error');
    } finally {
      setIsLoading(false);
    }
  }, [handlePollingResponse, forceStopPolling]);
  const startWorkflow = useCallback(async (config: any): Promise<WorkflowStartResponse> => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await workflowApi.startWorkflow(config);
      // 检查启动响应中的错误
      handlePollingResponse(response, 'workflow start');
      setCurrentSession(response.session_id);
      // 启动后立即获取一次状态
      setTimeout(() => {
        if (response.session_id) {
          fetchWorkflowStatus(response.session_id);
        }
      }, 1000);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start workflow';
      setError(errorMessage);
      handlePollingResponse({ error: errorMessage }, 'workflow start error');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchWorkflowStatus, handlePollingResponse]);
  const stopWorkflow = useCallback(async (id: string, force: boolean = false) => {
    try {
      setIsLoading(true);
      await workflowApi.stopWorkflow(id, force);
      forceStopPolling('Workflow stopped by user');
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to stop workflow';
      setError(errorMessage);
      handlePollingResponse({ error: errorMessage }, 'workflow stop error');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [forceStopPolling, handlePollingResponse]);
  // Poll for status updates with configurable interval
  useEffect(() => {
    if (currentSession && isPolling) {
      fetchWorkflowStatus(currentSession);
      // 使用配置的工作流轮询间隔
      const workflowInterval = pollingConfig?.intervals?.workflow || 3000; // 默认3秒
      const interval = setInterval(() => {
        fetchWorkflowStatus(currentSession);
      }, workflowInterval * 1000); // 转换为毫秒
      return () => clearInterval(interval);
    }
  }, [currentSession, isPolling, fetchWorkflowStatus, pollingConfig]);
  return {
    workflowStatus,
    currentSession,
    activeSessions,
    isLoading,
    error,
    mrInfo,
    startWorkflow,
    stopWorkflow,
    fetchWorkflowStatus
  };
};