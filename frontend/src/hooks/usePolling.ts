import { useState, useEffect, useRef } from 'react';
import { configApi } from '../services/workflow-api';

interface PollingConfig {
  enabled: boolean;
  intervals: {
    dashboard: number;
    pipeline: number;
    logs: number;
    status: number;
    workflow: number;
  };
}

export const usePolling = () => {
  const [isPolling, setIsPolling] = useState(true);
  const [pollingConfig, setPollingConfig] = useState(null);
  const [shouldStopPolling, setShouldStopPolling] = useState(false);
  const [stopReason, setStopReason] = useState(null);
  const errorDetectedRef = useRef(false);
  const lastLogLinesRef = useRef([]);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const config = await configApi.getPollingConfig();
        setPollingConfig({
          enabled: true,
          intervals: {
            dashboard: Math.max(config.default_interval || 5, 3), // 最少3秒
            pipeline: Math.max(config.pipeline_interval || 2, 2), // 最少2秒
            logs: Math.max(config.log_interval || 10, 5), // 最少5秒
            status: Math.max(config.default_interval || 3, 3), // 最少3秒
            workflow: Math.max(config.workflow_interval || 5, 5) // 最少5秒，默认5秒轮询工作流状态
          }
        });
        console.log('Polling config loaded:', {
          workflow: Math.max(config.workflow_interval || 5, 5),
          pipeline: Math.max(config.pipeline_interval || 2, 2),
          dashboard: Math.max(config.default_interval || 5, 3)
        });
      } catch (error) {
        console.error('Failed to fetch polling config:', error);
        // Use safer defaults with minimum intervals
        setPollingConfig({
          enabled: true,
          intervals: {
            dashboard: 5,   // 5秒
            pipeline: 3,    // 3秒
            logs: 10,       // 10秒
            status: 5,      // 5秒
            workflow: 5     // 5秒 - 工作流状态轮询间隔
          }
        });
        console.log('Using default polling config with safe intervals');
      }
    };

    fetchConfig();
  }, []);

  // 检查日志中是否包含致命错误
  const checkLogsForFatalErrors = (logs: string[]): {hasFatal: boolean, errorMessage: string} => {
    if (!logs || logs.length === 0) return {hasFatal: false, errorMessage: ''};
    
    // 保存最新的几行日志用于检测
    lastLogLinesRef.current = [...lastLogLinesRef.current, ...logs].slice(-20);
    
    // 致命错误关键词列表
    const fatalKeywords = [
      'fatal:',
      'fatal error',
      'unencrypted http is not supported',
      'authentication failed',
      'permission denied',
      'repository not found',
      'connection refused',
      'access denied',
      'could not read from remote repository'
    ];
    
    // 检查最近的日志行
    for (const line of lastLogLinesRef.current) {
      const lowerLine = line.toLowerCase();
      for (const keyword of fatalKeywords) {
        if (lowerLine.includes(keyword)) {
          // 提取完整的错误消息
          return {
            hasFatal: true,
            errorMessage: line.trim()
          };
        }
      }
    }
    
    return {hasFatal: false, errorMessage: ''};
  };

  // 检测错误信息并停止轮询
  const checkForErrors = (data: any): boolean => {
    if (!data) return false;

    // 检查日志信息
    if (data.logs && Array.isArray(data.logs)) {
      const {hasFatal, errorMessage} = checkLogsForFatalErrors(data.logs);
      if (hasFatal) {
        setStopReason(errorMessage);
        return true;
      }
    }

    // 检查工作流状态
    if (data.status === 'failed') {
      return true;
    }

    // 检查常见的错误字段
    const errorFields = [
      'error_message',
      'error',
      'message'
    ];

    for (const field of errorFields) {
      if (data[field]) {
        const errorMsg = data[field];
        // 检查是否包含fatal错误关键词
        const fatalKeywords = [
          'fatal:',
          'fatal error',
          'unencrypted http is not supported',
          'authentication failed',
          'permission denied',
          'repository not found',
          'connection refused',
          'access denied',
          'unauthorized',
          'forbidden'
        ];

        if (typeof errorMsg === 'string') {
          const lowerMsg = errorMsg.toLowerCase();
          if (fatalKeywords.some(keyword => lowerMsg.includes(keyword))) {
            return true;
          }
        }

        // 检查是否包含其他错误关键词
        const errorKeywords = [
          'not found',
          'failed',
          'error',
          'timeout',
          'invalid',
          'cannot',
          'unable',
          'expired'
        ];

        if (typeof errorMsg === 'string' && 
            errorKeywords.some(keyword => 
              errorMsg.toLowerCase().includes(keyword)
            )) {
          return true;
        }
      }
    }

    // 检查步骤错误
    if (data.steps) {
      for (const [stepName, stepData] of Object.entries(data.steps)) {
        if (stepData && typeof stepData === 'object') {
          const step = stepData as any;
          if (step.status === 'failed' && step.error_message) {
            return true;
          }
        }
      }
    }

    // 检查HTTP状态码
    if (data.status_code && typeof data.status_code === 'number') {
      if (data.status_code >= 400) {
        return true;
      }
    }

    return false;
  };

  const handlePollingResponse = (data: any, context?: string) => {
    if (errorDetectedRef.current) return; // 已经检测到错误，不再处理

    if (checkForErrors(data)) {
      errorDetectedRef.current = true;
      setShouldStopPolling(true);
      setIsPolling(false);

      // 提取错误信息
      let errorMsg = 'Unknown error detected';
      if (data.error_message) {
        errorMsg = data.error_message;
      } else if (data.error) {
        errorMsg = data.error;
      } else if (data.message) {
        errorMsg = data.message;
      } else if (data.status === 'failed') {
        errorMsg = 'Workflow failed';
      }

      setStopReason(errorMsg);
      console.warn(`Polling stopped due to error in ${context || 'response'}:`, errorMsg);
    }

    // 检查工作流完成状态
    if (data.status && ['completed', 'cancelled'].includes(data.status)) {
      setShouldStopPolling(true);
      setIsPolling(false);
      setStopReason(`Workflow ${data.status}`);
    }
  };

  const togglePolling = () => {
    if (shouldStopPolling) {
      // 如果因为错误停止，需要重置状态
      errorDetectedRef.current = false;
      setShouldStopPolling(false);
      setStopReason(null);
    }
    setIsPolling(!isPolling);
  };

  const forceStopPolling = (reason?: string) => {
    errorDetectedRef.current = true;
    setShouldStopPolling(true);
    setIsPolling(false);
    setStopReason(reason || 'Manually stopped');
  };

  const resetPolling = () => {
    errorDetectedRef.current = false;
    setShouldStopPolling(false);
    setStopReason(null);
    setIsPolling(true);
  };

  return {
    isPolling: isPolling && !shouldStopPolling,
    pollingConfig,
    shouldStopPolling,
    stopReason,
    togglePolling,
    forceStopPolling,
    resetPolling,
    handlePollingResponse,
    checkForErrors,
    checkLogsForFatalErrors
  };
};