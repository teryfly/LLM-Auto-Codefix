import { useState, useEffect, useCallback } from 'react';
import { workflowApi } from '../services/workflow-api';
import { usePolling } from './usePolling';
interface WorkflowStatus {
  session_id: string;
  status: string;
  current_step: string;
  steps: Record<string, any>;
  project_info?: any;
  pipeline_info?: any;
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
export const useWorkflow = (sessionId?: string) => {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [currentSession, setCurrentSession] = useState<string | null>(sessionId || null);
  const [activeSessions, setActiveSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isPolling } = usePolling();
  const fetchWorkflowStatus = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      const status = await workflowApi.getWorkflowStatus(id);
      setWorkflowStatus(status);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch workflow status:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch workflow status');
      // 不要在错误时清空 workflowStatus，保持上一次的状态
    } finally {
      setIsLoading(false);
    }
  }, []);
  const startWorkflow = useCallback(async (config: any) => {
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
    startWorkflow,
    stopWorkflow,
    fetchWorkflowStatus
  };
};