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
  const { isPolling } = usePolling();
  const fetchPipelineStatus = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      const response = await apiClient.get(`/pipeline/${id}/status`);
      setPipelineStatus(response);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch pipeline status:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch pipeline status');
      setPipelineStatus(null);
    } finally {
      setIsLoading(false);
    }
  }, []);
  const fetchJobStatuses = useCallback(async (id: string) => {
    try {
      const response = await apiClient.get(`/pipeline/${id}/jobs`);
      setJobStatuses(response.jobs || []);
    } catch (err) {
      console.error('Failed to fetch job statuses:', err);
      setJobStatuses([]);
    }
  }, []);
  const fetchMonitorData = useCallback(async (id: string) => {
    try {
      const response = await apiClient.get(`/pipeline/${id}/monitor`);
      setMonitorData(response);
    } catch (err) {
      console.error('Failed to fetch monitor data:', err);
      setMonitorData(null);
    }
  }, []);
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
    refreshPipeline: () => {
      if (sessionId) {
        fetchPipelineStatus(sessionId);
        fetchJobStatuses(sessionId);
        fetchMonitorData(sessionId);
      }
    }
  };
};