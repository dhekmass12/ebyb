import React from 'react';
import { MessageSquareText, LogOut, User } from 'lucide-react';

export default function Navbar({ clientId, clientName, onLogout }) {
  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <div className="brand-icon-box">
            <MessageSquareText size={22} />
          </div>
          <div>
            <span style={{ color: '#0f172a' }}>DigiChat</span>
            <span style={{ color: '#2563eb', marginLeft: '4px' }}>Billing</span>
          </div>
        </div>

        {clientId && (
          <div className="navbar-actions">
            <div className="active-user-badge" title={`Sesi aktif Client ID: ${clientId}`}>
              <div className="user-dot" />
              <User size={15} style={{ color: '#2563eb' }} />
              <span>
                {clientName ? clientName : clientId} ({clientId})
              </span>
            </div>

            <button
              onClick={onLogout}
              className="btn-logout"
              title="Keluar dan hapus sesi Client ID dari Local Storage"
            >
              <LogOut size={15} />
              <span>Keluar</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
