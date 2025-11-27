-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_deals INTEGER DEFAULT 0,
    successful_deals INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Advertisements table
CREATE TABLE IF NOT EXISTS advertisements (
    id BIGSERIAL PRIMARY KEY,
    seller_telegram_id BIGINT NOT NULL,
    currency_type VARCHAR(50) NOT NULL,
    amount DECIMAL(18,8) NOT NULL,
    price_per_unit DECIMAL(18,2) NOT NULL,
    min_order DECIMAL(18,8),
    max_order DECIMAL(18,8),
    payment_methods TEXT[],
    description TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deals table
CREATE TABLE IF NOT EXISTS deals (
    id BIGSERIAL PRIMARY KEY,
    advertisement_id BIGINT NOT NULL,
    buyer_telegram_id BIGINT NOT NULL,
    seller_telegram_id BIGINT NOT NULL,
    amount DECIMAL(18,8) NOT NULL,
    total_price DECIMAL(18,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'created' CHECK (status IN ('created', 'paid', 'disputed', 'completed', 'cancelled')),
    escrow_status VARCHAR(20) DEFAULT 'holding' CHECK (escrow_status IN ('holding', 'released', 'refunded')),
    payment_confirmed_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id BIGSERIAL PRIMARY KEY,
    deal_id BIGINT NOT NULL,
    reviewer_telegram_id BIGINT NOT NULL,
    reviewed_telegram_id BIGINT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(deal_id, reviewer_telegram_id)
);

-- Messages table (for in-deal chat)
CREATE TABLE IF NOT EXISTS deal_messages (
    id BIGSERIAL PRIMARY KEY,
    deal_id BIGINT NOT NULL,
    sender_telegram_id BIGINT NOT NULL,
    message_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Support tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL,
    deal_id BIGINT,
    subject VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Support messages table
CREATE TABLE IF NOT EXISTS support_messages (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    sender_telegram_id BIGINT NOT NULL,
    message_text TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_advertisements_seller ON advertisements(seller_telegram_id);
CREATE INDEX IF NOT EXISTS idx_advertisements_status ON advertisements(status);
CREATE INDEX IF NOT EXISTS idx_deals_buyer ON deals(buyer_telegram_id);
CREATE INDEX IF NOT EXISTS idx_deals_seller ON deals(seller_telegram_id);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deal_messages_deal ON deal_messages(deal_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_user ON support_tickets(user_telegram_id);
CREATE INDEX IF NOT EXISTS idx_support_messages_ticket ON support_messages(ticket_id);