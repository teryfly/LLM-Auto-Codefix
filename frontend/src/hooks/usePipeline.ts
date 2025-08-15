import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../services/api-client';
import { usePolling } from './usePolling';
interface PipelineStatus {
  pipeline_id?: number;
  status?: string;
  ref?: string;
  web_url?: string;
  created_at?: string;
  updated_at?: string;
}
interface JobStatus {
  id: number;
  name: string;
  status: string;
  stage: string;
  created_at?: string;
  started_at?: string;
  finished_at?: string;
  web_url?: string;
}
interface MonitorData {
  pipeline?: PipelineStatus;
  jobs?: JobStatus[];
  deployment_url?: string;
}
export const usePipeline = (sessionId?: string) => {
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [jobStatuses, setJobStatuses] = useState<JobStatus[]>([]);
  const [monitorData, setMonitorData] = useState<MonitorData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isPolling, handlePollingResponse } = usePolling();
  const fetchPipelineStatus = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      const response = await apiClient.get(`/pipeline/${id}/status`);
      // 检查响应中的错误信息
      handlePollingResponse(response, 'pipeline status');
      setPipelineStatus(response);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch pipeline status:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch pipeline status';
      setError(errorMessage);
      setPipelineStatus(null);
      // 检查错误并停止轮询
      handlePollingResponse({ error: errorMessage }, 'pipeline status error');
    } finally {
      setIsLoading(false);
    }
  }, [handlePollingResponse]);
  const fetchJobStatuses = useCallback(async (id: string) => {
    try {
      const response = await apiClient.get(`/pipeline/${id}/jobs`);
      // 检查响应中的错误信息
      handlePollingResponse(response, 'job statuses');
      setJobStatuses(response.jobs || []);
    } catch (err) {
      console.error('Failed to fetch job statuses:', err);
      setJobStatuses([]);
      // 检查错误
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch job statuses';
      handlePollingResponse({ error: errorMessage }, 'job statuses error');
    }
  }, [handlePollingResponse]);
  const fetchMonitorData = useCallback(async (id: string) => {
    try {
      const response = await apiClient.get(`/pipeline/${id}/monitor`);
      // 检查响应中的错误信息
      handlePollingResponse(response, 'monitor data');
      setMonitorData(response);
    } catch (err) {
      console.error('Failed to fetch monitor data:', err);
      setMonitorData(null);
      // 检查错误
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch monitor data';
      handlePollingResponse({ error: errorMessage }, 'monitor data error');
    }
  }, [handlePollingResponse]);
  const retryFailedJobs = useCallback(async () => {
    if (!sessionId) return;
    try {
      const response = await apiClient.post(`/pipeline/${sessionId}/retry`);
      handlePollingResponse(response, 'retry jobs');
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to retry jobs';
      handlePollingResponse({ error: errorMessage }, 'retry jobs error');
      throw err;
    }
  }, [sessionId, handlePollingResponse]);
  const getJobTrace = useCallback(async (jobId: number) => {
    if (!sessionId) return '';
    try {
      const response = await apiClient.get(`/pipeline/${sessionId}/trace/${jobId}`);
      handlePollingResponse(response, 'job trace');
      return response.trace || '';
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get job trace';
      handlePollingResponse({ error: errorMessage }, 'job trace error');
      return `Error loading trace: ${errorMessage}`;
    }
  }, [sessionId, handlePollingResponse]);
  // Poll for pipeline updates
  useEffect(() => {
    if (sessionId && isPolling) {
      // Initial fetch
      fetchPipelineStatus(sessionId);
      fetchJobStatuses(sessionId);
      fetchMonitorData(sessionId);
      // Set up polling interval
      const interval = setInterval(() => {
        fetchPipelineStatus(sessionId);
        fetchJobStatuses(sessionId);
        fetchMonitorData(sessionId);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [sessionId, isPolling, fetchPipelineStatus, fetchJobStatuses, fetchMonitorData]);
  return {
    pipelineStatus,
    jobStatuses,
    monitorData,
    isLoading,
    error,
    retryFailedJobs,
    getJobTrace,
    refreshPipeline: () => {
      if (sessionId) {
        fetchPipelineStatus(sessionId);
        fetchJobStatuses(sessionId);
        fetchMonitorData(sessionId);
      }
    }
  };
};