import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';
import { usePolling } from '../../hooks/usePolling';
import { PollingIndicator } from '../common/PollingIndicator';
import './Layout.css';

interface LayoutProps {
  children?: React.ReactNode;
}

export const Layout: React.FC = ({ children }) => {
  const { isPolling, pollingConfig } = usePolling();

  return (
    <div className="layout">
      <Header />
      <Sidebar />
        <main>
          <Outlet />
          {children || <div>Content goes here</div>}
        </main>
      <Footer />
      {isPolling && <PollingIndicator config={pollingConfig} />}
    </div>
  );
};