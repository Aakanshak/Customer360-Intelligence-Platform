CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    age INTEGER CHECK (age BETWEEN 16 AND 110),
    gender VARCHAR(32),
    city VARCHAR(128),
    state VARCHAR(128),
    signup_date DATE NOT NULL,
    email VARCHAR(255) UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(128) NOT NULL,
    category VARCHAR(128) NOT NULL,
    unit_price NUMERIC(14,2) NOT NULL CHECK (unit_price >= 0),
    unit_cost NUMERIC(14,2) NOT NULL CHECK (unit_cost >= 0)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    order_amount NUMERIC(14,2) NOT NULL CHECK (order_amount >= 0),
    cost_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    order_date TIMESTAMP NOT NULL,
    channel VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'completed'
);

CREATE INDEX IF NOT EXISTS ix_transactions_customer_date ON transactions(customer_id, order_date DESC);
CREATE INDEX IF NOT EXISTS ix_transactions_order_date ON transactions(order_date);
CREATE INDEX IF NOT EXISTS ix_customers_state ON customers(state);
CREATE INDEX IF NOT EXISTS ix_products_category ON products(category);

CREATE TABLE IF NOT EXISTS marketing_activities (
    campaign_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    campaign_name VARCHAR(128),
    campaign_response BOOLEAN NOT NULL DEFAULT FALSE,
    channel VARCHAR(64),
    campaign_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    touched_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    issue_type VARCHAR(128),
    resolution_time NUMERIC(10,2),
    ticket_status VARCHAR(64) NOT NULL DEFAULT 'closed',
    satisfaction_score NUMERIC(3,1),
    opened_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP
);
