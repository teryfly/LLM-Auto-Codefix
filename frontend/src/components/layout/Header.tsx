import React from 'react';
import { useWorkflow } from '../../hooks/useWorkflow';
import { StatusBadge } from '../common/StatusBadge';
import './Header.css';

export const Header: React.FC = () => {
  const { currentSession, workflowStatus } = useWorkflow();

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="logo">
          🤖 LLM Auto Codefix
        </div>
        <div className="session-info">
          {currentSession && (
            <span>
              Session: {currentSession.slice(0, 8)}...
            </span>
          )}
        </div>
        <div className="actions">
          <button onClick={() => window.location.reload()} title="Refresh page">🔄</button>
          <button onClick={() => window.open('/api/docs', '_blank')} title="API Documentation">📚</button>
        </div>
      </div>
    </header>
  );
};