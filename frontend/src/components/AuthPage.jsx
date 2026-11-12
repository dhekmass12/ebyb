import React, { useState } from 'react';
import { ShieldCheck, KeyRound, User, Eye, EyeOff, AlertCircle, ArrowRight, Loader2 } from 'lucide-react';
import { loginClient } from '../services/api';

export default function AuthPage({ onLoginSuccess }) {
  const [clientId, setClientId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setErrorMessage('');

    if (!clientId.trim()) {
      setErrorMessage('Client ID wajib diisi!');
      return;
    }

    setLoading(true);
    try {
      const data = await loginClient(clientId.trim(), password);
      if (data && data.success && data.client) {
        localStorage.setItem('client_id', data.client.client_id);
        localStorage.setItem('client_name', data.client.client_name || '');
        localStorage.setItem('company_name', data.client.company_name || '');

        onLoginSuccess(data.client);
      } else {
        setErrorMessage('Gagal memvalidasi Client ID');
      }
    } catch (err) {
      setErrorMessage(
        err.message || 'Client ID tidak ditemukan. Silakan periksa kembali.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card animate-slide-up">
        <div className="auth-header">
          <div className="auth-logo">
            <ShieldCheck size={32} />
          </div>
          <h1>Masuk ke Portal</h1>
          <p>Masukkan Client ID dan kata sandi akun Anda untuk melanjutkan</p>
        </div>

        {errorMessage && (
          <div className="auth-error-alert animate-fade-in" style={{ marginBottom: '1.25rem' }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="auth-form">
          <div className="form-group">
            <label htmlFor="clientId">Client ID</label>
            <div className="input-wrapper">
              <User className="input-icon" size={18} />
              <input
                id="clientId"
                type="text"
                className="form-control"
                placeholder="Masukkan Client ID"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                autoComplete="off"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <KeyRound className="input-icon" size={18} />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className="form-control"
                placeholder="Masukkan password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="toggle-password-btn"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: '0.5rem' }}>
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Memvalidasi...</span>
              </>
            ) : (
              <>
                <span>Masuk</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
