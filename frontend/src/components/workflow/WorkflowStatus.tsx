import React from 'react';
import { StatusBadge } from '../common/StatusBadge';
import './WorkflowStatus.css';

interface WorkflowStatusData {
  session_id?: string;
  status?: string;
  current_step?: string;
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
}

interface PipelineStatusData {
  pipeline_id?: number;
  status?: string;
  ref?: string;
  web_url?: string;
}

interface CIStatusData {
  merge_request: {
    id: number;
    iid: number;
    title: string;
    state: string;
    source_branch: string;
    target_branch: string;
    web_url: string;
  };
  pipeline?: {
    id: number;
    status: string;
    ref: string;
    web_url: string;
    created_at?: string;
    updated_at?: string;
  };
  jobs: Array;
  overall_status: string;
}

interface WorkflowStatusProps {
  status?: WorkflowStatusData | null;
  pipelineStatus?: PipelineStatusData | null;
  ciStatus?: CIStatusData | null;
  isRecovered?: boolean;
  mrExists?: boolean | null;
  shouldStopPolling?: boolean;
}

export const WorkflowStatus: React.FC = ({
  status = null,
  pipelineStatus = null,
  ciStatus = null,
  isRecovered = false,
  mrExists = null,
  shouldStopPolling = false
}) => {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return 'Invalid Date';
    }
  };

  const getExecutionTime = () => {
    if (!status?.started_at) return null;
    try {
      const start = new Date(status.started_at);
      const end = status.updated_at ? new Date(status.updated_at) : new Date();
      const diffMs = end.getTime() - start.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffSecs = Math.floor((diffMs % 60000) / 1000);
      return `${diffMins}m ${diffSecs}s`;
    } catch {
      return 'N/A';
    }
  };

  // 计算Job统计信息
  const getJobStats = () => {
    if (!ciStatus?.jobs || ciStatus.jobs.length === 0) {
      return null;
    }
    const total = ciStatus.jobs.length;
    const completed = ciStatus.jobs.filter(job => 
      ['success', 'failed', 'canceled', 'skipped'].includes(job.status)
    ).length;
    const failed = ciStatus.jobs.filter(job => job.status === 'failed').length;
    const running = ciStatus.jobs.filter(job => 
      ['running', 'pending'].includes(job.status)
    ).length;
    return { total, completed, failed, running };
  };

  const jobStats = getJobStats();

  // 检查是否有错误信息需要显示
  const hasError = status?.error_message || status?.status === 'failed';
  const errorMessage = status?.error_message || (status?.status === 'failed' ? 'Workflow failed' : null);

  // 如果MR不存在，显示错误状态
  if (mrExists === false) {
    return (
      
        
          Workflow Status
          
        
        
          Merge Request Not Found
          
            ❌
            
              The specified Merge Request could not be found. Please verify the MR ID and project name.
            
          
        
      
    );
  }

  // 如果没有状态数据，显示占位符
  if (!status && !ciStatus) {
    return (
      
        
          Workflow Status
          
        
        
          
            No workflow data available. Start a workflow to see status information.
          
        
      
    );
  }

  return (
    
      
        Workflow Status
        
          
          {isRecovered && (
            
              🔄 Recovered
            
          )}
          {shouldStopPolling && (
            
              ⏹️ Monitoring Stopped
            
          )}
          {hasError && (
            
              ❌ Error Detected
            
          )}
        
      

      {/* 错误提示区域 */}
      {hasError && (
        
          
            🚨
            
              Workflow Error: {errorMessage}
              {shouldStopPolling && (
                
                  Monitoring has been stopped due to this error. Please check the logs for more details.
                
              )}
            
          
        
      )}

      {isRecovered && !hasError && (
        
          
            🔍
            
              Status Recovery Mode: This workflow status has been recovered 
              from GitLab MR information. The system is actively checking CI/CD progress 
              to provide real-time updates.
            
          
        
      )}

      
        
          
            General Information
            
              
                Session ID:
                
                  {status?.session_id || 'N/A'}
                
              
              
                Status:
                
                  
                  {status?.status || ciStatus?.overall_status || 'Unknown'}
                  {isRecovered &&  (Recovered)}
                
              
              
                Current Step:
                {status?.current_step || 'N/A'}
              
              
                Started:
                {formatDate(status?.started_at)}
              
              
                Last Updated:
                {formatDate(status?.updated_at)}
              
              {getExecutionTime() && (
                
                  Execution Time:
                  {getExecutionTime()}
                
              )}
            
          

          {status?.project_info && (
            
              Project Information
              
                
                  Project Name:
                  {status.project_info.project_name || 'N/A'}
                
                {status.project_info.project_id && (
                  
                    Project ID:
                    {status.project_info.project_id}
                  
                )}
                {status.project_info.local_dir && (
                  
                    Local Directory:
                    
                      {status.project_info.local_dir}
                    
                  
                )}
              
            
          )}

          {(ciStatus?.pipeline || pipelineStatus) && (
            
              Pipeline Information
              
                
                  Pipeline ID:
                  
                    {ciStatus?.pipeline?.id || pipelineStatus?.pipeline_id || 'N/A'}
                  
                
                
                  Pipeline Status:
                  
                    
                    {ciStatus?.pipeline?.status || pipelineStatus?.status || 'Unknown'}
                  
                
                
                  Branch:
                  
                    {ciStatus?.pipeline?.ref || pipelineStatus?.ref || 'N/A'}
                  
                
                {(ciStatus?.pipeline?.web_url || pipelineStatus?.web_url) && (
                  
                    Pipeline URL:
                    
                      
                        View in GitLab 🔗
                      
                    
                  
                )}
                {status?.pipeline_info?.deployment_url && (
                  
                    Deployment URL:
                    
                      
                        🚀 View Deployment
                      
                    
                  
                )}
              
            
          )}

          {(ciStatus?.merge_request || status?.pipeline_info?.merge_request) && (
            
              Merge Request Information
              
                
                  MR ID:
                  
                    
                      {ciStatus?.merge_request?.iid || status?.pipeline_info?.merge_request?.iid || 
                       ciStatus?.merge_request?.id || status?.pipeline_info?.merge_request?.id}
                    
                  
                
                {(ciStatus?.merge_request?.title || status?.pipeline_info?.merge_request?.title) && (
                  
                    Title:
                    
                      {ciStatus?.merge_request?.title || status?.pipeline_info?.merge_request?.title}
                    
                  
                )}
                {ciStatus?.merge_request?.state && (
                  
                    State:
                    
                      
                      {ciStatus.merge_request.state}
                    
                  
                )}
                {(ciStatus?.merge_request?.source_branch && ciStatus?.merge_request?.target_branch) && (
                  
                    Branches:
                    
                      {ciStatus.merge_request.source_branch} → {ciStatus.merge_request.target_branch}
                    
                  
                )}
                {(ciStatus?.merge_request?.web_url || status?.pipeline_info?.merge_request?.web_url) && (
                  
                    MR URL:
                    
                      
                        View MR in GitLab 🔗
                      
                    
                  
                )}
              
            
          )}

          {jobStats && (
            
              CI/CD Jobs Summary
              
                
                  Total Jobs:
                  {jobStats.total}
                
                
                  Completed:
                  {jobStats.completed}
                
                
                  Failed:
                  
                     0 ? 'text-danger' : ''}>
                      {jobStats.failed}
                    
                  
                
                
                  Running:
                  {jobStats.running}
                
                
                  Progress:
                  
                    {Math.round((jobStats.completed / jobStats.total) * 100)}%
                  
                
              
            
          )}
        

        {/* 详细错误信息 */}
        {hasError && errorMessage && (
          
            Error Details
            
              ⚠️
              
                {errorMessage}
                {shouldStopPolling && (
                  
                    Next Steps:
                    
                      Check the error message above for specific details
                      Verify your GitLab repository URL and authentication
                      Ensure the repository uses HTTPS instead of HTTP
                      Check network connectivity and firewall settings
                    
                  
                )}
              
            
          
        )}
      
    
  );
};