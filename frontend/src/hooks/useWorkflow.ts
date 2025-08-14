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
  const { isPolling } = usePolling();
  const fetchWorkflowStatus = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      const status = await workflowApi.getWorkflowStatus(id);
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
      setError(null);
    } catch (err) {
      console.error('Failed to fetch workflow status:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch workflow status');
    } finally {
      setIsLoading(false);
    }
  }, []);
  const startWorkflow = useCallback(async (config: any): Promise<WorkflowStartResponse> => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await workflowApi.startWorkflow(config);
      setCurrentSession(response.session_id);
      // 启动后立即获取一次状态
      setTimeout(() => {
        if (response.session_id) {
          fetchWorkflowStatus(response.session_id);
        }
      }, 1000);
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start workflow');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchWorkflowStatus]);
  const stopWorkflow = useCallback(async (id: string, force: boolean = false) => {
    try {
      setIsLoading(true);
      await workflowApi.stopWorkflow(id, force);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop workflow');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);
  // Poll for status updates
  useEffect(() => {
    if (currentSession && isPolling) {
      fetchWorkflowStatus(currentSession);
      const interval = setInterval(() => {
        fetchWorkflowStatus(currentSession);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [currentSession, isPolling, fetchWorkflowStatus]);
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