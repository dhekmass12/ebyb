import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot, Sparkles, RefreshCw, Loader2 } from 'lucide-react';
import { sendChatMessage, fetchConversationMessages, deleteConversation } from '../services/api';

const INITIAL_MESSAGES = [
  {
    id: 1,
    sender: 'assistant',
    text: 'Halo! Saya asisten virtual layanan digital. Ada yang dapat saya bantu mengenai tagihan, paket website, atau layanan SEO Anda hari ini?',
    time: 'Baru saja',
  },
];

const SUGGESTIONS = [
  'Berapa sisa tagihan saya?',
  'Informasi paket layanan SEO',
  'Minta nomor rekening BCA.',
  'Tolong aktivasi domain resmi saya sekarang',
  'Apakah tersedia layanan sewa drone?',
];

export default function ChatbotWidget({ clientId: propClientId, clientName }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [inputText, setInputText] = useState('');
  const [conversationId, setConversationId] = useState(() => {
    return localStorage.getItem('conversation_id') || '';
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Ambil client_id secara otomatis dari local storage (fallback ke props)
  const activeClientId = localStorage.getItem('client_id') || propClientId || '';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversationHistory = async (convId) => {
    setIsLoading(true);
    try {
      const chatList = await fetchConversationMessages(convId);
      if (Array.isArray(chatList) && chatList.length > 0) {
        // Urutkan berdasarkan turn_index
        const sorted = [...chatList].sort((a, b) => (a.turn_index || 0) - (b.turn_index || 0));
        const formatted = sorted.map((item) => ({
          id: item.id || `${item.turn_index}-${Math.random()}`,
          sender: item.sender,
          text: item.message_text,
          turn_index: item.turn_index,
          time: item.created_at
            ? new Date(item.created_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
            : 'Tercatat',
        }));
        setMessages(formatted);
      } else {
        setMessages(INITIAL_MESSAGES);
      }
    } catch (err) {
      console.warn('Tidak dapat mengambil riwayat percakapan lama, memulai sesi baru:', err.message);
      setMessages(INITIAL_MESSAGES);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen, isTyping]);

  // Efek saat Chatbot dibuka: sinkronkan riwayat chat jika sesi sudah ada
  useEffect(() => {
    if (!isOpen || !activeClientId) return;

    const storageKey = `conversation_id_${activeClientId}`;
    const currentConvId = localStorage.getItem('conversation_id') || localStorage.getItem(storageKey);

    if (currentConvId) {
      loadConversationHistory(currentConvId);
    }
  }, [isOpen, activeClientId]);

  // Handler tombol chatbot: Pastikan pembuatan conversation_id baru di local storage saat tombol ditekan jika belum ada
  const handleToggleChatbot = () => {
    const nextOpen = !isOpen;
    if (nextOpen && activeClientId) {
      const storageKey = `conversation_id_${activeClientId}`;
      let currentConvId = localStorage.getItem('conversation_id') || localStorage.getItem(storageKey);
      if (!currentConvId) {
        // Kriteria 1: Jika tidak ada conversation_id di local storage, buat yang baru ketika user menekan tombol chatbot
        currentConvId = `conv-${Math.random().toString(36).substring(2, 10)}`;
        localStorage.setItem('conversation_id', currentConvId);
        localStorage.setItem(storageKey, currentConvId);
        setConversationId(currentConvId);
        setMessages(INITIAL_MESSAGES);
      } else {
        localStorage.setItem('conversation_id', currentConvId);
        localStorage.setItem(storageKey, currentConvId);
        setConversationId(currentConvId);
      }
    }
    setIsOpen(nextOpen);
  };

  const handleResetConversation = async () => {
    if (!activeClientId) return;
    const storageKey = `conversation_id_${activeClientId}`;
    const oldConvId = localStorage.getItem('conversation_id') || conversationId;
    if (oldConvId) {
      try {
        await deleteConversation(oldConvId);
      } catch (err) {
        console.warn('Gagal menghapus percakapan di server:', err.message);
      }
    }
    const newConvId = `conv-${Math.random().toString(36).substring(2, 10)}`;
    localStorage.setItem('conversation_id', newConvId);
    localStorage.setItem(storageKey, newConvId);
    setConversationId(newConvId);
    setMessages(INITIAL_MESSAGES);
  };

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputText;
    if (!text.trim() || isTyping) return;

    if (!activeClientId) {
      alert('Sesi Anda tidak ditemukan. Silakan login kembali.');
      return;
    }

    // Pastikan conversation_id diambil dari local storage
    const storageKey = `conversation_id_${activeClientId}`;
    let convIdToSend = localStorage.getItem('conversation_id') || localStorage.getItem(storageKey) || conversationId;
    if (!convIdToSend) {
      convIdToSend = `conv-${Math.random().toString(36).substring(2, 10)}`;
      localStorage.setItem('conversation_id', convIdToSend);
      localStorage.setItem(storageKey, convIdToSend);
      setConversationId(convIdToSend);
    }

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: text.trim(),
      time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsTyping(true);

    try {
      // Memanggil endpoint /chat dengan client_id, conversation_id (dari local storage), dan message
      const result = await sendChatMessage(activeClientId, convIdToSend, text.trim());

      // Update conversation_id jika backend mengembalikan atau memperbarui ID
      const resolvedConvId = result.conversation_id || convIdToSend;
      setConversationId(resolvedConvId);
      localStorage.setItem('conversation_id', resolvedConvId);
      localStorage.setItem(storageKey, resolvedConvId);

      const botMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: result.response,
        time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      let errMsg = err.message || 'Gagal memproses pesan.';
      if (err.status === 404) {
        errMsg = `Client atau sesi tidak ditemukan (404 Not Found): ${errMsg}`;
      } else if (err.status === 403) {
        errMsg = `Akses ditolak (403 Forbidden): ${errMsg}`;
      } else if (err.status === 400) {
        errMsg = `Permintaan tidak valid (400 Bad Request): ${errMsg}`;
      }
      const errorMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: `Maaf, terjadi kesalahan: ${errMsg}`,
        time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Tombol Floating Icon Chatbot di Pojok Kanan Bawah */}
      <button
        type="button"
        className="chatbot-launcher-btn"
        onClick={handleToggleChatbot}
        aria-label="Toggle AI Chatbot"
        title={isOpen ? 'Tutup Chatbot' : 'Buka AI Chatbot Assistant'}
      >
        <div className="chatbot-launcher-pulse" />
        {isOpen ? <X size={26} /> : <MessageSquare size={26} />}
      </button>

      {/* Floating Chatbot Window */}
      {isOpen && (
        <div className="chatbot-window animate-slide-up">
          {/* Header */}
          <div className="chatbot-header">
            <div className="chatbot-header-info">
              <div className="bot-avatar">
                <Bot size={20} />
              </div>
              <div>
                <div className="bot-name">AI Assistant</div>
                <div className="bot-status">
                  <span className="bot-status-dot" />
                  <span>Online • Sesi {clientName ? `${clientName} (${activeClientId})` : activeClientId || 'Guest'}</span>
                </div>
              </div>
            </div>

            <div className="chatbot-header-actions">
              <button
                type="button"
                onClick={handleResetConversation}
                title="Mulai percakapan baru"
                style={{ marginRight: 6 }}
              >
                <RefreshCw size={16} />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Tutup Chat"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Body / Message History */}
          <div className="chatbot-messages">
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '30px 0', color: '#6b7280' }}>
                <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 8px' }} />
                <p style={{ fontSize: '0.85rem' }}>Memuat riwayat chat...</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`chat-bubble-wrapper ${msg.sender === 'user' ? 'user' : 'assistant'} animate-fade-in`}
                >
                  <div
                    className={`chat-bubble ${msg.sender === 'user' ? 'user' : 'assistant'}`}
                    style={{ whiteSpace: 'pre-wrap' }}
                  >
                    {msg.text}
                  </div>
                  <span className="chat-time">{msg.time}</span>
                </div>
              ))
            )}

            {isTyping && (
              <div className="chat-bubble-wrapper assistant animate-fade-in">
                <div className="chat-bubble assistant" style={{ fontStyle: 'italic', color: '#6b7280' }}>
                  <Loader2 size={14} className="animate-spin" style={{ display: 'inline', marginRight: 6 }} />
                  Asisten sedang mengetik...
                </div>
              </div>
            )}

            {/* Quick Suggestion Chips */}
            {messages.length <= 2 && !isLoading && (
              <div className="chatbot-suggestions">
                {SUGGESTIONS.map((sug, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="suggestion-chip"
                    onClick={() => handleSendMessage(sug)}
                  >
                    <Sparkles size={12} style={{ display: 'inline', marginRight: 4 }} />
                    {sug}
                  </button>
                ))}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Footer Input */}
          <div className="chatbot-footer">
            <input
              type="text"
              className="chatbot-input"
              placeholder="Ketik pertanyaan untuk asisten..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isTyping}
            />
            <button
              type="button"
              className="chatbot-send-btn"
              onClick={() => handleSendMessage()}
              disabled={!inputText.trim() || isTyping}
              title="Kirim pesan"
            >
              <Send size={18} />
            </button>
          </div>

          <div className="chatbot-disclaimer">
            Sesi ID: {conversationId || '-'} • Didukung Gemini Tool Calling Engine
          </div>
        </div>
      )}
    </>
  );
}
