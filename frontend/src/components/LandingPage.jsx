import React, { useState, useEffect } from 'react';
import {
  Users,
  FileText,
  DollarSign,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Phone,
  Globe,
  ChevronRight,
  Info,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { fetchClients, fetchClientInvoices, fetchBillingSummary } from '../services/api';

const formatIDR = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(value || 0);
};

export default function LandingPage({ activeClientId, onSwitchSession }) {
  const [clients, setClients] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [billingSummary, setBillingSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal when clicking another client
  const [selectedForeignClient, setSelectedForeignClient] = useState(null);
  // Highlight invoice section trigger
  const [invoiceHighlighted, setInvoiceHighlighted] = useState(false);

  // Ambil client_id dari local storage secara eksplisit sesuai instruksi
  const storedClientId = localStorage.getItem('client_id') || activeClientId;

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const clientsData = await fetchClients();
        if (isMounted) setClients(clientsData || []);

        if (storedClientId) {
          const [invoicesData, billingData] = await Promise.all([
            fetchClientInvoices(storedClientId),
            fetchBillingSummary(storedClientId),
          ]);
          if (isMounted) {
            setInvoices(invoicesData || []);
            setBillingSummary(billingData);
          }
        }
      } catch (err) {
        console.error('Error fetching data:', err);
        if (isMounted) {
          setError(err.message || 'Gagal memuat data dari server. Pastikan backend FastAPI sedang berjalan di port 8000.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, [storedClientId, refreshTrigger]);

  const handleRefresh = () => setRefreshTrigger((prev) => prev + 1);

  // Handler ketika salah satu client di klik
  const handleClientClick = (client) => {
    // Sesuai ketentuan:
    // "Ketika client di klik, akan muncul berbagai invoice milik client tersebut.
    // Invoice milik client didapat dari mencocokkan kolom "client_id" di tabel "invoices" dengan client_id di local storage!"
    if (client.client_id === storedClientId) {
      // Client yang diklik cocok dengan local storage: tampilkan invoice
      setInvoiceHighlighted(true);
      const el = document.getElementById('invoices-section');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      setTimeout(() => setInvoiceHighlighted(false), 2000);
    } else {
      // User mengklik client lain: jelaskan aturan pencocokan local storage dan tawarkan ganti sesi
      setSelectedForeignClient(client);
    }
  };

  const handleSwitchToClickedClient = (client) => {
    localStorage.setItem('client_id', client.client_id);
    localStorage.setItem('client_name', client.client_name || '');
    localStorage.setItem('company_name', client.company_name || '');
    setSelectedForeignClient(null);
    if (onSwitchSession) {
      onSwitchSession(client);
    }
  };

  const currentClient = clients.find((c) => c.client_id === storedClientId);

  // Hitung total ringkasan
  const totalAmount = invoices.reduce((sum, item) => sum + (item.total_amount || 0), 0);
  const totalPaid = invoices.reduce((sum, item) => sum + (item.amount_paid || 0), 0);
  const totalBalance = invoices.reduce((sum, item) => sum + (item.outstanding_balance || 0), 0);

  return (
    <div className="landing-content animate-fade-in">
      {/* Hero Welcome Banner */}
      <div className="hero-banner">
        <div className="hero-text">
          <h1>Selamat Datang, {currentClient ? currentClient.client_name : storedClientId}!</h1>
          <p>
            Portal manajemen layanan digital dan pemantauan status tagihan Anda. Klik pada kartu client
            di bawah untuk memeriksa detail invoice.
          </p>
          <div className="session-badge">
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#60a5fa' }} />
            <span>Local Storage Active Session: <strong>{storedClientId}</strong></span>
          </div>
        </div>
        <div>
          <button
            onClick={handleRefresh}
            className="btn-primary"
            style={{ background: 'rgba(255, 255, 255, 0.15)', backdropFilter: 'blur(5px)', border: '1px solid rgba(255, 255, 255, 0.2)' }}
            title="Muat ulang data"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            <span>Segarkan Data</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="auth-error-alert animate-fade-in" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={20} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Summary Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">
            <Users size={24} />
          </div>
          <div className="stat-details">
            <span className="stat-label">Akun Sesi Aktif</span>
            <span className="stat-value">{storedClientId}</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
            <FileText size={24} />
          </div>
          <div className="stat-details">
            <span className="stat-label">Total Nilai Tagihan</span>
            <span className="stat-value">{formatIDR(totalAmount)}</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <CheckCircle2 size={24} />
          </div>
          <div className="stat-details">
            <span className="stat-label">Total Terbayar</span>
            <span className="stat-value">{formatIDR(billingSummary?.total_payment ?? totalPaid)}</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon amber">
            <DollarSign size={24} />
          </div>
          <div className="stat-details">
            <span className="stat-label">Sisa Tagihan</span>
            <span className="stat-value">{formatIDR(billingSummary?.total_outstanding_balance ?? totalBalance)}</span>
          </div>
        </div>
      </div>

      {/* Section 1: Daftar Client */}
      <div className="section-header">
        <h2 className="section-title">
          <Users size={22} style={{ color: '#2563eb' }} />
          <span>Daftar Client (Tabel "clients")</span>
        </h2>
        <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
          Total {clients.length} klien terdaftar di database
        </span>
      </div>

      {loading && clients.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
          <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 1rem auto', color: '#3b82f6' }} />
          <p>Memuat daftar client dari database...</p>
        </div>
      ) : (
        <div className="clients-grid">
          {clients.map((client) => {
            const isActive = client.client_id === storedClientId;
            return (
              <div
                key={client.client_id}
                className={`client-card ${isActive ? 'is-active-client' : ''}`}
                onClick={() => handleClientClick(client)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleClientClick(client);
                }}
              >
                <div className="client-card-top">
                  <span className="client-id-pill">{client.client_id}</span>
                  {isActive && (
                    <span className="active-pill">
                      <Sparkles size={12} />
                      <span>Akun Anda</span>
                    </span>
                  )}
                </div>

                <div>
                  <h3 className="client-name">{client.client_name}</h3>
                  <div className="client-company">{client.company_name || '-'}</div>

                  <div className="client-meta-list">
                    <div className="meta-row">
                      <Phone size={14} style={{ color: '#94a3b8' }} />
                      <span>{client.phone_number || '-'}</span>
                    </div>
                    {client.official_domain && (
                      <div className="meta-row">
                        <Globe size={14} style={{ color: '#94a3b8' }} />
                        <span>{client.official_domain}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="client-card-action">
                  <span>{isActive ? 'Lihat Invoices Anda' : 'Klik untuk Tampilkan Invoice'}</span>
                  <ChevronRight size={16} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Section 2: Invoices Milik Client */}
      <div
        id="invoices-section"
        className="invoices-section animate-fade-in"
        style={{
          border: invoiceHighlighted ? '2px solid #3b82f6' : '1px solid #e2e8f0',
          boxShadow: invoiceHighlighted ? '0 0 20px rgba(59, 130, 246, 0.3)' : '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
          transition: 'all 0.3s ease',
        }}
      >
        <div className="invoices-header">
          <div className="invoices-title">
            <h2>Daftar Invoice Milik Client</h2>
            <div className="invoices-match-rule">
              <Info size={15} style={{ color: '#2563eb' }} />
              <span>
                Invoice ditampilkan dari pencocokan kolom <strong>client_id</strong> di tabel <em>invoices</em> dengan
                client_id di <strong>Local Storage</strong>: <code style={{ color: '#2563eb' }}>{storedClientId}</code>
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            {billingSummary && (
              <span
                style={{
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  padding: '0.35rem 0.75rem',
                  borderRadius: '9999px',
                  background: billingSummary.valid ? '#d1fae5' : '#fee2e2',
                  color: billingSummary.valid ? '#065f46' : '#991b1b',
                }}
              >
                {billingSummary.valid ? '✓ Status Billing Valid' : `⚠ Inkonsistensi pada ${billingSummary.invoice_no}`}
              </span>
            )}
          </div>
        </div>

        {invoices.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#64748b' }}>
            <FileText size={48} style={{ margin: '0 auto 1rem auto', color: '#cbd5e1' }} />
            <h4 style={{ color: '#1e293b', marginBottom: '0.5rem' }}>Tidak Ada Invoice Ditemukan</h4>
            <p style={{ fontSize: '0.9rem' }}>
              Tidak ditemukan invoice dengan client_id "{storedClientId}" di database.
            </p>
          </div>
        ) : (
          <div className="invoices-table-container">
            <table className="invoices-table">
              <thead>
                <tr>
                  <th>No. Invoice</th>
                  <th>Client ID</th>
                  <th>Jenis Layanan</th>
                  <th>Nama Paket</th>
                  <th>Total Tagihan</th>
                  <th>Sudah Dibayar</th>
                  <th>Sisa Tagihan</th>
                  <th>Status Pembayaran</th>
                  <th>Jatuh Tempo</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => {
                  let statusClass = 'badge-unpaid';
                  let statusLabel = 'Belum Lunas';
                  if (inv.payment_status === 'paid') {
                    statusClass = 'badge-paid';
                    statusLabel = 'Lunas';
                  } else if (inv.payment_status === 'half_paid') {
                    statusClass = 'badge-half_paid';
                    statusLabel = 'Sebagian';
                  }

                  return (
                    <tr key={inv.invoice_no}>
                      <td style={{ fontWeight: 700, color: '#2563eb' }}>{inv.invoice_no}</td>
                      <td>
                        <span style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: 4, fontSize: '0.8rem', fontWeight: 600 }}>
                          {inv.client_id}
                        </span>
                      </td>
                      <td style={{ textTransform: 'uppercase', fontSize: '0.8rem', fontWeight: 600 }}>
                        {inv.service_type}
                      </td>
                      <td style={{ fontWeight: 500 }}>{inv.package_name}</td>
                      <td style={{ fontWeight: 600 }}>{formatIDR(inv.total_amount)}</td>
                      <td style={{ color: '#059669', fontWeight: 600 }}>{formatIDR(inv.amount_paid)}</td>
                      <td style={{ color: inv.outstanding_balance > 0 ? '#d97706' : '#64748b', fontWeight: 700 }}>
                        {formatIDR(inv.outstanding_balance)}
                      </td>
                      <td>
                        <span className={`badge ${statusClass}`}>
                          {statusLabel} ({inv.payment_status})
                        </span>
                      </td>
                      <td style={{ color: '#64748b', fontSize: '0.825rem' }}>
                        {inv.due_date || '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Dialog Ketika User Mengklik Client Lain */}
      {selectedForeignClient && (
        <div className="modal-overlay animate-fade-in" onClick={() => setSelectedForeignClient(null)}>
          <div className="modal-content animate-slide-up" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: '#fef3c7', color: '#d97706', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <AlertTriangle size={24} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.15rem', color: '#0f172a' }}>Pemberitahuan Akses Invoice</h3>
                <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Ketentuan Sistem Sesi Local Storage</span>
              </div>
            </div>

            <p style={{ fontSize: '0.9rem', color: '#475569', lineHeight: 1.5, marginBottom: '1.25rem' }}>
              Anda saat ini masuk dengan sesi <strong>Client ID: {storedClientId}</strong>.
              <br /><br />
              Sesuai ketentuan, daftar invoice yang ditampilkan diperoleh dari mencocokkan kolom
              <em> "client_id"</em> di tabel <em>invoices</em> dengan <strong>client_id di local storage</strong>.
              <br /><br />
              Apakah Anda ingin beralih sesi login ke <strong>{selectedForeignClient.client_name} ({selectedForeignClient.client_id})</strong> agar invoice miliknya dapat dimuat dari local storage?
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <button
                type="button"
                className="btn-primary"
                onClick={() => handleSwitchToClickedClient(selectedForeignClient)}
              >
                <span>Beralih ke Sesi {selectedForeignClient.client_id} & Tampilkan Invoice</span>
                <ChevronRight size={16} />
              </button>

              <button
                type="button"
                onClick={() => setSelectedForeignClient(null)}
                style={{
                  padding: '0.7rem',
                  borderRadius: 10,
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  color: '#64748b',
                  background: '#f1f5f9',
                }}
              >
                Tetap di Sesi Saat Ini ({storedClientId})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
