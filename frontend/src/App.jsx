import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import AuthPage from './components/AuthPage';
import LandingPage from './components/LandingPage';
import ChatbotWidget from './components/ChatbotWidget';
import './App.css';

export default function App() {
  const [clientId, setClientId] = useState(() => localStorage.getItem('client_id') || '');
  const [clientName, setClientName] = useState(() => localStorage.getItem('client_name') || '');

  // Sinkronisasi jika local storage berubah
  useEffect(() => {
    const handleStorageChange = () => {
      const storedId = localStorage.getItem('client_id') || '';
      const storedName = localStorage.getItem('client_name') || '';
      setClientId(storedId);
      setClientName(storedName);
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const handleLoginSuccess = (client) => {
    setClientId(client.client_id);
    setClientName(client.client_name || '');
    const clientConv = localStorage.getItem(`conversation_id_${client.client_id}`);
    if (clientConv) {
      localStorage.setItem('conversation_id', clientConv);
    } else {
      localStorage.removeItem('conversation_id');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('client_id');
    localStorage.removeItem('client_name');
    localStorage.removeItem('company_name');
    localStorage.removeItem('conversation_id');
    setClientId('');
    setClientName('');
  };

  const handleSwitchSession = (client) => {
    setClientId(client.client_id);
    setClientName(client.client_name || '');
    const clientConv = localStorage.getItem(`conversation_id_${client.client_id}`);
    if (clientConv) {
      localStorage.setItem('conversation_id', clientConv);
    } else {
      localStorage.removeItem('conversation_id');
    }
  };

  return (
    <div className="app-container">
      {clientId ? (
        <>
          <Navbar clientId={clientId} clientName={clientName} onLogout={handleLogout} />
          <LandingPage activeClientId={clientId} onSwitchSession={handleSwitchSession} />
          {/* Chatbot yang ditampilkan ketika klik icon di pojok kanan bawah */}
          <ChatbotWidget clientId={clientId} clientName={clientName} />
        </>
      ) : (
        <AuthPage onLoginSuccess={handleLoginSuccess} />
      )}
    </div>
  );
}
