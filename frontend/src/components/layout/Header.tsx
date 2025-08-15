import React from 'react';
import './Header.css';
export const Header: React.FC = () => {
  return (
    <header className="app-header">
      <div className="header-content">
        <div className="logo">
          🤖 LLM Auto Codefix
        </div>
      </div>
    </header>
  );
};