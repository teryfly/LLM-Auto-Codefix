import React from 'react';
import './PollingIndicator.css';

interface PollingIndicatorProps {
  isActive: boolean;
  interval: number;
}

export const PollingIndicator: React.FC = ({
  isActive,
  interval
}) => {
  return (
    <div className="polling-indicator">
      <span>{isActive ? `Live (${interval}s)` : 'Paused'}</span>
    </div>
  );
};