import { useState, useEffect, useCallback } from 'react';
import { workflowApi } from '../services/workflow-api';
import { usePolling } from './usePolling';

interface WorkflowStatus {
  session_id: string;
  status: string;
  current_step: string;
  steps: Record;
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
  logs?: string[];
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
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [currentSession, setCurrentSession] = useState(sessionId || null);
  const [activeSessions, setActiveSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mrInfo, setMrInfo] = useState(null);
  const [logs, setLogs] = useState([]);

  const { 
    isPolling, 
    handlePollingResponse, 
    forceStopPolling, 
    pollingConfig, 
    checkLogsForFatalErrors 
  } = usePolling();

  const fetchWorkflowStatus = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      
      // Use the combined status+logs method
      const response = await workflowApi.getWorkflowStatusWithLogs(id);
      
      // Extract logs if present
      if (response.logs && Array.isArray(response.logs)) {
        setLogs(prevLogs => {
          // Filter out duplicates
          const newLogs = response.logs.filter(log => !prevLogs.includes(log));
          return [...prevLogs, ...newLogs];
        });
        
        // Check logs for fatal errors
        const { hasFatal, errorMessage } = checkLogsForFatalErrors(response.logs);
        if (hasFatal) {
          setError(errorMessage);
          forceStopPolling(`Fatal error: ${errorMessage}`);
          
          // Update status with error message
          if (response) {
            response.error_message = errorMessage;
            response.status = 'failed';
            
            // Update current step with error
            if (response.steps && response.current_step) {
              const currentStep = response.steps[response.current_step];
              if (currentStep) {
                currentStep.status = 'failed';
                currentStep.error_message = errorMessage;
              }
            }
          }
        }
      }
      
      // Check response for errors
      handlePollingResponse(response, 'workflow status');
      
      setWorkflowStatus(response);

      // 提取MR信息
      if (response.pipeline_info?.merge_request) {
        const mr = response.pipeline_info.merge_request;
        const projectName = response.project_info?.project_name?.replace('/', '-');
        setMrInfo({
          mrId: mr.iid?.toString() || mr.id?.toString(),
          projectName: projectName,
          webUrl: mr.web_url
        });
      }

      // 检查是否应该停止轮询
      if (response.status === 'completed' || response.status === 'failed' || response.status === 'cancelled') {
        forceStopPolling(`Workflow ${response.status}`);
      }

      // 检查错误信息
      if (response.error_message) {
        setError(response.error_message);
        forceStopPolling(`Workflow error: ${response.error_message}`);
      }

      // 检查步骤错误信息
      if (response.steps) {
        for (const [stepName, stepData] of Object.entries(response.steps)) {
          if (stepData.status === 'failed' && stepData.error_message) {
            setError(stepData.error_message);
            // 如果是关键步骤失败，立即停止轮询
            if (stepName === 'prepare_project' || stepName === 'merge_mr') {
              forceStopPolling(`Step ${stepName} failed: ${stepData.error_message}`);
              break;
            }
          }
        }
      }

    } catch (err) {
      console.error('Failed to fetch workflow status:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch workflow status';
      setError(errorMessage);
      // 检查错误并停止轮询
      handlePollingResponse({ error: errorMessage }, 'workflow API error');
    } finally {
      setIsLoading(false);
    }
  }, [handlePollingResponse, forceStopPolling, checkLogsForFatalErrors]);

  const startWorkflow = useCallback(async (config: any) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await workflowApi.startWorkflow(config);
      
      // 检查启动响应中的错误
      handlePollingResponse(response, 'workflow start');
      
      setCurrentSession(response.session_id);

      // 启动后立即获取一次状态，延迟稍长一些让后台有时间初始化
      setTimeout(() => {
        if (response.session_id) {
          fetchWorkflowStatus(response.session_id);
        }
      }, 2000); // 延迟2秒

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
    if (currentSession && isPolling && pollingConfig) {
      // 使用配置的工作流轮询间隔，确保最少5秒
      const workflowInterval = Math.max(pollingConfig.intervals.workflow || 5, 5);
      
      console.log(`Setting up workflow polling with ${workflowInterval}s interval for session ${currentSession}`);
      
      // 初始获取，延迟1秒让后台有时间处理
      const initialTimeout = setTimeout(() => {
        fetchWorkflowStatus(currentSession);
      }, 1000);
      
      // 设置轮询间隔
      const interval = setInterval(() => {
        console.log(`Polling workflow status for session ${currentSession}`);
        fetchWorkflowStatus(currentSession);
      }, workflowInterval * 1000); // 转换为毫秒

      return () => {
        console.log('Clearing workflow polling interval and initial timeout');
        clearTimeout(initialTimeout);
        clearInterval(interval);
      };
    }
  }, [currentSession, isPolling, fetchWorkflowStatus, pollingConfig]);

  return {
    workflowStatus,
    currentSession,
    activeSessions,
    isLoading,
    error,
    mrInfo,
    logs,
    startWorkflow,
    stopWorkflow,
    fetchWorkflowStatus
  };
};