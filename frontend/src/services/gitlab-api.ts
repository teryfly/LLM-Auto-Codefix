import { apiClient } from './api-client';
export const gitlabApi = {
  getProjectInfo: (projectName: string) =>
    apiClient.get(`/gitlab/projects/${encodeURIComponent(projectName.replace('/', '%2F'))}`),
  getMergeRequestInfo: (projectName: string, mrId: string) =>
    apiClient.get(`/gitlab/projects/${encodeURIComponent(projectName.replace('/', '%2F'))}/merge_requests/${mrId}`),
  getMergeRequestPipelines: (projectName: string, mrId: string) =>
    apiClient.get(`/gitlab/projects/${encodeURIComponent(projectName.replace('/', '%2F'))}/merge_requests/${mrId}/pipelines`),
  getMergeRequestCIStatus: (projectName: string, mrId: string) =>
    apiClient.get(`/gitlab/projects/${encodeURIComponent(projectName.replace('/', '%2F'))}/merge_requests/${mrId}/ci_status`),
  getJobTrace: (projectName: string, pipelineId: string, jobId: string) =>
    apiClient.get(`/gitlab/projects/${encodeURIComponent(projectName.replace('/', '%2F'))}/pipelines/${pipelineId}/jobs/${jobId}/trace`),
};
// 管道相关的API
export const pipelineApi = {
  getPipelineStatus: (sessionId: string) =>
    apiClient.get(`/pipeline/${sessionId}/status`),
  getJobStatuses: (sessionId: string) =>
    apiClient.get(`/pipeline/${sessionId}/jobs`),
  getMonitorData: (sessionId: string) =>
    apiClient.get(`/pipeline/${sessionId}/monitor`),
};
export default gitlabApi;