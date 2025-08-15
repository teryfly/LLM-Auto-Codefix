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
  const [pollingConfig, setPollingConfig] = useState<PollingConfig | null>(null);
  const [shouldStopPolling, setShouldStopPolling] = useState(false);
  const [stopReason, setStopReason] = useState<string | null>(null);
  const errorDetectedRef = useRef(false);
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const config = await configApi.getPollingConfig();
        setPollingConfig({
          enabled: true,
          intervals: {
            dashboard: config.default_interval,
            pipeline: config.pipeline_interval,
            logs: config.log_interval,
            status: config.default_interval,
            workflow: config.default_interval
          }
        });
      } catch (error) {
        console.error('Failed to fetch polling config:', error);
        // Use defaults
        setPollingConfig({
          enabled: true,
          intervals: {
            dashboard: 5,
            pipeline: 2,
            logs: 10,
            status: 3,
            workflow: 3
          }
        });
      }
    };
    fetchConfig();
  }, []);
  // 检测错误信息并停止轮询
  const checkForErrors = (data: any): boolean => {
    if (!data) return false;
    // 检查常见的错误字段
    const errorFields = [
      'error_message',
      'error',
      'message'
    ];
    for (const field of errorFields) {
      if (data[field]) {
        const errorMsg = data[field];
        // 检查是否包含错误关键词
        const errorKeywords = [
          'not found',
          'failed',
          'error',
          'timeout',
          'invalid',
          'unauthorized',
          'forbidden',
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
    // 检查状态字段
    if (data.status && typeof data.status === 'string') {
      const errorStatuses = ['failed', 'error', 'timeout', 'cancelled', 'expired'];
      if (errorStatuses.includes(data.status.toLowerCase())) {
        return true;
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
      const errorMsg = data.error_message || data.error || data.message || 'Unknown error detected';
      setStopReason(errorMsg);
      console.warn(`Polling stopped due to error in ${context || 'response'}:`, errorMsg);
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
    checkForErrors
  };
};