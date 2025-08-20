import { apiClient } from './api-client';

export const llmApi = {
  // 流式分析Pipeline日志
  analyzeLogsStream: (data: {
    project_id?: number;
    job_id?: number;
    logs?: string;
  }) => {
    return fetch('/api/v1/llm/analyze-logs-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
  },

  // 流式代码修复
  fixCodeStream: (prompt: string) => {
    return fetch('/api/v1/llm/fix-code-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt })
    });
  },

  // 获取Job日志
  getJobLogs: (projectId: number, jobId: number) =>
    apiClient.get(`/llm/job-logs/${projectId}/${jobId}`),

  // 创建EventSource连接用于接收流式数据
  createEventSource: (url: string, data: any) => {
    const params = new URLSearchParams();
    Object.keys(data).forEach(key => {
      if (data[key] !== undefined && data[key] !== null) {
        params.append(key, String(data[key]));
      }
    });
    
    return new EventSource(`${url}?${params.toString()}`);
  }
};

export default llmApi;