// API Client for Digital Chatbot & Billing Portal
const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Helper to handle fetch responses
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'Terjadi kesalahan pada server';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorData.message || errorDetail;
    } catch {
      // ignore json parse error
    }
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

/**
 * Autentikasi user dengan Client ID
 */
export async function loginClient(clientId, password = '') {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: clientId.trim(), password }),
  });
  return handleResponse(res);
}

/**
 * Mengambil seluruh daftar client
 */
export async function fetchClients() {
  const res = await fetch(`${BASE_URL}/clients`);
  return handleResponse(res);
}

/**
 * Mengambil detail client berdasarkan client_id
 */
export async function fetchClientById(clientId) {
  const res = await fetch(`${BASE_URL}/clients/${encodeURIComponent(clientId)}`);
  return handleResponse(res);
}

/**
 * Mengambil daftar invoice untuk client_id tertentu
 * (Mencocokkan client_id di tabel invoices)
 */
export async function fetchClientInvoices(clientId) {
  const res = await fetch(`${BASE_URL}/clients/${encodeURIComponent(clientId)}/invoices`);
  return handleResponse(res);
}

/**
 * Mengambil ringkasan billing untuk client_id
 */
export async function fetchBillingSummary(clientId) {
  try {
    const res = await fetch(`${BASE_URL}/billing/${encodeURIComponent(clientId)}`);
    return await handleResponse(res);
  } catch (err) {
    console.warn(`Could not fetch billing summary for ${clientId}:`, err.message);
    return null;
  }
}

/**
 * Mengirim pesan ke chatbot AI endpoint /chat
 */
export async function sendChatMessage(clientId, conversationId, message) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: clientId,
      conversation_id: conversationId || undefined,
      message: message,
    }),
  });
  return handleResponse(res);
}

/**
 * Mengambil histori pesan chat berdasarkan conversation_id
 */
export async function fetchConversationMessages(conversationId) {
  const res = await fetch(`${BASE_URL}/conversations/${encodeURIComponent(conversationId)}`);
  const data = await handleResponse(res);
  return data.messages || [];
}

/**
 * Menghapus sesi percakapan
 */
export async function deleteConversation(conversationId) {
  const res = await fetch(`${BASE_URL}/conversations/${encodeURIComponent(conversationId)}`, {
    method: 'DELETE',
  });
  return handleResponse(res);
}

