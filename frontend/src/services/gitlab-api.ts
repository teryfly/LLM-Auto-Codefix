import { apiClient } from './api-client';

export const pipelineApi = {
  getPipelineStatus: (sessionId: string) =>
    apiClient.get(`/pipeline/${sessionId}/status`),

  getJobStatuses: (sessionId: string) =>
    apiClient.get(`/pipeline/${sessionId}/jobs`),

  getMonitorData: (sessionId: string) =>
    apiClient.get(`/pipeline/${sessionId}/monitor`),

  retryFailedJobs: (sessionId: string) =>
    apiClient.post(`/pipeline/${sessionId}/retry`),

  getJobTrace: (sessionId: string, jobId: number) =>
    apiClient.get(`/pipeline/${sessionId}/trace/${jobId}`),
};