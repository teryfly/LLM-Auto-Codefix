import { apiClient } from './api-client';

export const workflowApi = {
  startWorkflow: (config: any) =>
    apiClient.post('/workflow/start', config),
  
  getWorkflowStatus: (sessionId: string) =>
    apiClient.get(`/workflow/status/${sessionId}`),
  
  getWorkflowStatusByMR: (projectName: string, mrId: string) =>
    apiClient.get(`/workflow/mr/${projectName}/${mrId}`),
  
  stopWorkflow: (sessionId: string, force: boolean = false) =>
    apiClient.post(`/workflow/stop/${sessionId}`, { force }),
  
  getWorkflowLogs: (sessionId: string) =>
    apiClient.get(`/workflow/logs/${sessionId}`),
    
  // New method to get both status and logs in a single request
  getWorkflowStatusWithLogs: async (sessionId: string) => {
    const status = await apiClient.get(`/workflow/status/${sessionId}`);
    try {
      // Try to get logs too
      const logsResponse = await apiClient.get(`/workflow/logs/${sessionId}`);
      return { ...status, logs: logsResponse.logs || [] };
    } catch (e) {
      // If logs fail, still return status
      return status;
    }
  }
};

export const configApi = {
  getPollingConfig: () =>
    apiClient.get('/config/polling'),
  updatePollingConfig: (config: any) =>
    apiClient.put('/config/polling', config),
  getAppConfig: () =>
    apiClient.get('/config/app'),
};