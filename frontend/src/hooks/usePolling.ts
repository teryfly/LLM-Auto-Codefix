import { useState, useEffect } from 'react';
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

  const togglePolling = () => {
    setIsPolling(!isPolling);
  };

  return {
    isPolling,
    pollingConfig,
    togglePolling
  };
};