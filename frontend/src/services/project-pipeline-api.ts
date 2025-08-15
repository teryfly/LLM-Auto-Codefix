import { apiClient } from './api-client';
export const projectPipelineApi = {
  // 获取项目信息
  getProjectInfo: (projectName: string) =>
    apiClient.get(`/projects/${encodeURIComponent(projectName.replace('/', '%2F'))}`),
  // 获取最新 Pipeline
  getLatestPipeline: (projectId: number) =>
    apiClient.get(`/projects/${projectId}/pipelines?per_page=1`),
  // 获取指定 Pipeline
  getPipeline: (projectId: number, pipelineId: number) =>
    apiClient.get(`/projects/${projectId}/pipelines/${pipelineId}`),
  // 获取 Pipeline 下的所有 Jobs
  getPipelineJobs: (projectId: number, pipelineId: number) =>
    apiClient.get(`/projects/${projectId}/pipelines/${pipelineId}/jobs`),
  // 获取 Job 信息
  getJob: (projectId: number, jobId: number) =>
    apiClient.get(`/projects/${projectId}/jobs/${jobId}`),
  // 获取 Job 日志
  getJobTrace: (projectId: number, jobId: number) =>
    apiClient.get(`/projects/${projectId}/jobs/${jobId}/trace`),
  // 创建 Merge Request
  createMergeRequest: (projectId: number, data: {
    source_branch: string;
    target_branch: string;
    title: string;
  }) =>
    apiClient.post(`/projects/${projectId}/merge_requests`, data),
  // 合并 Merge Request
  mergeMergeRequest: (projectId: number, mergeRequestIid: number, data?: {
    should_remove_source_branch?: boolean;
    merge_when_pipeline_succeeds?: boolean;
  }) =>
    apiClient.put(`/projects/${projectId}/merge_requests/${mergeRequestIid}/merge`, data),
};
export default projectPipelineApi;