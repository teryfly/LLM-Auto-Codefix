import { useState, useEffect } from 'react';
import { configApi } from '../services/workflow-api';

interface AppConfig {
  services?: {
    gitlab_url?: string;
    llm_model?: string;
  };
}

export const useConfig = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const appConfig = await configApi.getAppConfig();
        setConfig(appConfig);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load configuration');
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  return { config, loading, error };
};