import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { usePolling } from '../../hooks/usePolling';
import './Layout.css';
interface LayoutProps {
  children?: React.ReactNode;
}
export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { shouldStopPolling, stopReason } = usePolling();
  return (
    <div className="layout">
      <Header />
      <main className="main-content">
        {shouldStopPolling && stopReason && (
          <div className="polling-stopped-notice">
            <div className="notice-content">
              <span className="notice-icon">⚠️</span>
              <span className="notice-text">
                监控已停止: {stopReason}
              </span>
            </div>
          </div>
        )}
        <Outlet />
        {children}
      </main>
    </div>
  );
};