-- ============================================================
-- Omni-Channel Retail Personalization Engine - DB Schema
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    age INT,
    gender VARCHAR(10),
    location VARCHAR(100),
    registration_date TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP,
    channel_preference VARCHAR(20) DEFAULT 'web', -- web, store, mobile
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    price DECIMAL(10,2),
    brand VARCHAR(100),
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    product_id UUID REFERENCES products(product_id),
    channel VARCHAR(20) NOT NULL, -- web, store, mobile
    quantity INT DEFAULT 1,
    amount DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    transaction_date TIMESTAMP DEFAULT NOW(),
    store_id VARCHAR(50),
    session_id VARCHAR(100)
);

-- Events (web/social activity)
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    event_type VARCHAR(50) NOT NULL, -- click, view, add_to_cart, like, share
    product_id UUID REFERENCES products(product_id),
    channel VARCHAR(20) NOT NULL,
    session_id VARCHAR(100),
    metadata JSONB,
    event_timestamp TIMESTAMP DEFAULT NOW()
);

-- Customer segments
CREATE TABLE IF NOT EXISTS customer_segments (
    segment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) UNIQUE,
    segment_label VARCHAR(50) NOT NULL, -- high_value, frequent_buyer, at_risk, new_customer
    cluster_id INT,
    rfm_score DECIMAL(5,2),
    recency_score INT,
    frequency_score INT,
    monetary_score INT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Recommendations
CREATE TABLE IF NOT EXISTS recommendations (
    rec_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    product_id UUID REFERENCES products(product_id),
    score DECIMAL(5,4),
    reason VARCHAR(200),
    offer_type VARCHAR(50), -- discount, bundle, new_arrival, trending
    discount_pct DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, clicked, converted
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Notification log
CREATE TABLE IF NOT EXISTS notifications (
    notif_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    rec_id UUID REFERENCES recommendations(rec_id),
    channel VARCHAR(20) NOT NULL, -- email, sms, push
    subject VARCHAR(200),
    body TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);


-- Indexes
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_timestamp ON events(event_timestamp);
CREATE INDEX idx_recommendations_user ON recommendations(user_id);
CREATE INDEX idx_segments_user ON customer_segments(user_id);

-- ============================================================
-- Sample seed data
-- ============================================================

INSERT INTO products (name, category, subcategory, price, brand, tags) VALUES
('Wireless Noise-Cancelling Headphones', 'Electronics', 'Audio', 149.99, 'SoundPro', ARRAY['audio','wireless','premium']),
('Running Shoes Pro X', 'Footwear', 'Sports', 89.99, 'SpeedRun', ARRAY['sports','running','comfort']),
('Organic Green Tea', 'Grocery', 'Beverages', 12.99, 'TeaLeaf', ARRAY['organic','health','tea']),
('Smart Watch Series 5', 'Electronics', 'Wearables', 299.99, 'TechWear', ARRAY['smartwatch','fitness','tech']),
('Yoga Mat Premium', 'Sports', 'Fitness', 45.00, 'ZenFit', ARRAY['yoga','fitness','wellness']),
('Gaming Mechanical Keyboard', 'Electronics', 'Computing', 129.99, 'TypePro', ARRAY['gaming','keyboard','rgb']),
('Vitamin D3 Supplement', 'Health', 'Vitamins', 18.99, 'VitaPlus', ARRAY['health','vitamins','supplement']),
('Denim Slim Fit Jeans', 'Apparel', 'Bottoms', 59.99, 'DenimCo', ARRAY['fashion','denim','casual']),
('Stainless Steel Water Bottle', 'Kitchen', 'Drinkware', 24.99, 'HydroLife', ARRAY['eco','hydration','outdoor']),
('Python Programming Book', 'Books', 'Technology', 39.99, 'TechBooks', ARRAY['education','programming','python']);
