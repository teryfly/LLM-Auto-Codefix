import { apiClient } from './api-client';

export const workflowApi = {
  startWorkflow: (config: any) =>
    apiClient.post('/workflow/start', config),

  getWorkflowStatus: (sessionId: string) =>
    apiClient.get(`/workflow/status/${sessionId}`),

  stopWorkflow: (sessionId: string, force: boolean = false) =>
    apiClient.post(`/workflow/stop/${sessionId}`, { force }),

  getWorkflowLogs: (sessionId: string) =>
    apiClient.get(`/workflow/logs/${sessionId}`),
};

export const configApi = {
  getPollingConfig: () =>
    apiClient.get('/config/polling'),

  updatePollingConfig: (config: any) =>
    apiClient.put('/config/polling', config),

  getAppConfig: () =>
    apiClient.get('/config/app'),
};