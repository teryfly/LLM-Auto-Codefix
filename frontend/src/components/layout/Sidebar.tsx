import React from 'react';
import { NavLink } from 'react-router-dom';
import { useWorkflow } from '../../hooks/useWorkflow';
import { StatusBadge } from '../common/StatusBadge';
import './Sidebar.css';

export const Sidebar: React.FC = () => {
  const { currentSession, workflowStatus, activeSessions } = useWorkflow();

  return (
    <div className="sidebar">
      <nav>
        <ul>
          <li>
            <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              🏠 Dashboard
            </NavLink>
          </li>
          {currentSession && (
            <li>
              <NavLink to="/pipeline-monitor" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                🔧 Pipeline Monitor
              </NavLink>
            </li>
          )}
        </ul>
      </nav>
      {workflowStatus && (
        <div className="workflow-status">
          <h3>Current Workflow</h3>
          <StatusBadge status={workflowStatus.status} />
          <p>Step: {workflowStatus.current_step}</p>
        </div>
      )}
      <div className="active-sessions">
        <h3>Active Sessions</h3>
        {activeSessions.length === 0 ? (
          <p>No active sessions</p>
        ) : (
          <ul>
            {activeSessions.slice(0, 5).map((session) => (
              <li key={session.id}>{session.id.slice(0, 8)}...</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};