import React from 'react';
import { useConfig } from '../../hooks/useConfig';
import './Footer.css';

export const Footer: React.FC = () => {
  const { config } = useConfig();

  return (
    <footer className="footer">
      <div className="content has-text-centered">
        <p>
          <strong>LLM Auto Codefix v1.0.0</strong> • AI-powered CI/CD debugging
        </p>
        {config && (
          <p>
            <strong>GitLab: {new URL(config.services?.gitlab_url || '').hostname}</strong> •
            <strong>Model: {config.services?.llm_model || 'Unknown'}</strong>
          </p>
        )}
        <div className="links">
          <a href="/api-docs">API Docs</a> •
          <a href="/health-check">Health Check</a>
        </div>
      </div>
    </footer>
  );
};