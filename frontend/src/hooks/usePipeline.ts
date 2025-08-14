import { useState, useEffect, useCallback } from 'react';
import { pipelineApi } from '../services/gitlab-api';
import { usePolling } from './usePolling';

interface PipelineStatus {
  session_id: string;
  pipeline_id?: number;
  project_id?: number;
  status: string;
  ref?: string;
  web_url?: string;
}

interface JobStatus {
  id: number;
  name: string;
  status: string;
  stage?: string;
  web_url?: string;
}

export const usePipeline = (sessionId?: string) => {
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [jobStatuses, setJobStatuses] = useState([]);
  const [monitorData, setMonitorData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { isPolling } = usePolling();

  const fetchPipelineStatus = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      const status = await pipelineApi.getPipelineStatus(id);
      setPipelineStatus(status);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pipeline status');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchJobStatuses = useCallback(async (id: string) => {
    try {
      const jobs = await pipelineApi.getJobStatuses(id);
      setJobStatuses(jobs);
    } catch (err) {
      console.error('Failed to fetch job statuses:', err);
    }
  }, []);

  const fetchMonitorData = useCallback(async (id: string) => {
    try {
      const data = await pipelineApi.getMonitorData(id);
      setMonitorData(data);
    } catch (err) {
      console.error('Failed to fetch monitor data:', err);
    }
  }, []);

  const retryFailedJobs = useCallback(async () => {
    if (!sessionId) return;
    try {
      await pipelineApi.retryFailedJobs(sessionId);
    } catch (err) {
      throw err;
    }
  }, [sessionId]);

  const getJobTrace = useCallback(async (jobId: number) => {
    if (!sessionId) return '';
    try {
      const response = await pipelineApi.getJobTrace(sessionId, jobId);
      return response.trace;
    } catch (err) {
      throw err;
    }
  }, [sessionId]);

  // Poll for updates
  useEffect(() => {
    if (sessionId && isPolling) {
      const fetchAll = async () => {
        await Promise.all([
          fetchPipelineStatus(sessionId),
          fetchJobStatuses(sessionId),
          fetchMonitorData(sessionId)
        ]);
      };

      fetchAll();
      const interval = setInterval(fetchAll, 2000);
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
    getJobTrace
  };
};