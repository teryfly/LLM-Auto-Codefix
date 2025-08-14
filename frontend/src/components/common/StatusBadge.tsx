import React from 'react';
import './StatusBadge.css';

interface StatusBadgeProps {
  status: string;
  size?: 'small' | 'medium' | 'large';
}

export const StatusBadge: React.FC = ({ status, size = 'medium' }) => {
  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
      case 'completed':
        return 'status-success';
      case 'failed':
      case 'error':
        return 'status-failed';
      case 'running':
      case 'active':
        return 'status-running';
      case 'pending':
      case 'created':
        return 'status-pending';
      case 'cancelled':
      case 'canceled':
        return 'status-cancelled';
      case 'skipped':
        return 'status-skipped';
      default:
        return 'status-unknown';
    }
  };

  return (
     <div className={`status-badge ${getStatusClass(status)} ${size}`}>
      {status}
     </div>
  );
};