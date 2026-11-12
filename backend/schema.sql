-- ==============================================================================
-- SCHEMA DEFINITION (SQLite)
-- Sistem Chatbot Layanan Digital & Billing Portal
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. Tabel clients
CREATE TABLE IF NOT EXISTS clients (
    client_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    company_name TEXT,
    phone_number TEXT NOT NULL,
    official_domain TEXT,
    created_at DATETIME NOT NULL
);

-- 2. Tabel invoices
CREATE TABLE IF NOT EXISTS invoices (
    invoice_no TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    service_type TEXT NOT NULL,
    package_name TEXT NOT NULL,
    total_amount INTEGER NOT NULL,
    amount_paid INTEGER NOT NULL,
    payment_status TEXT NOT NULL CHECK(payment_status IN ('unpaid', 'half_paid', 'paid')),
    due_date DATE NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_invoices_client_id ON invoices (client_id);

-- 3. Tabel knowledge_bases
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    keyword_triggers TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding TEXT NOT NULL
);

-- 4. Tabel conversations
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversations_client_id ON conversations (client_id);

-- 5. Tabel chat_messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    sender TEXT NOT NULL CHECK(sender IN ('user', 'assistant')),
    message_text TEXT NOT NULL,
    detected_intent TEXT,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id ON chat_messages (conversation_id);

-- View dan Trigger Kompatibilitas
CREATE VIEW IF NOT EXISTS conversation AS SELECT * FROM conversations;
CREATE VIEW IF NOT EXISTS chat_messagess AS SELECT * FROM chat_messages;

CREATE TRIGGER IF NOT EXISTS trg_insert_conversation
INSTEAD OF INSERT ON conversation
BEGIN
    INSERT INTO conversations (conversation_id, client_id, created_at, updated_at)
    VALUES (NEW.conversation_id, NEW.client_id, NEW.created_at, NEW.updated_at);
END;

CREATE TRIGGER IF NOT EXISTS trg_insert_chat_messagess
INSTEAD OF INSERT ON chat_messagess
BEGIN
    INSERT INTO chat_messages (conversation_id, turn_index, sender, message_text, detected_intent, created_at)
    VALUES (NEW.conversation_id, NEW.turn_index, NEW.sender, NEW.message_text, NEW.detected_intent, NEW.created_at);
END;
