-- =============================================================================
-- KISWARM6.0 Database Initialization Script
-- =============================================================================
-- This script initializes the KISWARM6.0 database with required tables
--
-- Author: Baron Marco Paolo Ialongo
-- Version: 6.0.0
-- =============================================================================

-- Set character set
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Use the database
USE kiswarm6;

-- =============================================================================
-- Users Table (M60 Authentication)
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    entity_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    metadata JSON,
    INDEX idx_entity_id (entity_id),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- Sessions Table (M60 Authentication)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- Accounts Table (M61 Banking)
-- =============================================================================

CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    iban VARCHAR(34) UNIQUE,
    account_type ENUM('checking', 'savings', 'investment') DEFAULT 'checking',
    currency VARCHAR(3) DEFAULT 'EUR',
    balance DECIMAL(15, 2) DEFAULT 0.00,
    available_balance DECIMAL(15, 2) DEFAULT 0.00,
    status ENUM('active', 'inactive', 'frozen', 'closed') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_account_number (account_number),
    INDEX idx_iban (iban)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- Transactions Table (M61 Banking)
-- =============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    account_id VARCHAR(36) NOT NULL,
    transaction_type ENUM('credit', 'debit', 'transfer', 'sepa') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    reference VARCHAR(255),
    description TEXT,
    counterparty_iban VARCHAR(34),
    counterparty_name VARCHAR(255),
    status ENUM('pending', 'completed', 'failed', 'reversed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    metadata JSON,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    INDEX idx_account_id (account_id),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- Reputation Table (M62 Investment)
-- =============================================================================

CREATE TABLE IF NOT EXISTS reputation (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    entity_id VARCHAR(255) NOT NULL UNIQUE,
    score INT DEFAULT 500 CHECK (score >= 0 AND score <= 1000),
    level ENUM('basic', 'bronze', 'silver', 'gold', 'platinum', 'diamond', 'elite') DEFAULT 'silver',
    daily_limit DECIMAL(15, 2) DEFAULT 10000.00,
    monthly_limit DECIMAL(15, 2) DEFAULT 100000.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_entity_id (entity_id),
    INDEX idx_score (score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- Reputation History Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS reputation_history (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    entity_id VARCHAR(255) NOT NULL,
    old_score INT NOT NULL,
    new_score INT NOT NULL,
    delta INT NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity_id (entity_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- Investments Table (M62 Investment)
-- =============================================================================

CREATE TABLE IF NOT EXISTS investments (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    investment_type VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    status ENUM('active', 'matured', 'withdrawn', 'cancelled') DEFAULT 'active',
    expected_return DECIMAL(5, 2),
    actual_return DECIMAL(5, 2),
    start_date DATE NOT NULL,
    maturity_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- Audit Log Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    entity_id VARCHAR(255),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),
    record_id VARCHAR(36),
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity_id (entity_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- KI-Proof Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS ki_proofs (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    entity_id VARCHAR(255) NOT NULL,
    proof_type VARCHAR(50) NOT NULL,
    proof_hash VARCHAR(255) NOT NULL,
    signature TEXT,
    verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    INDEX idx_entity_id (entity_id),
    INDEX idx_proof_hash (proof_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- Create Triggers for Audit Log
-- =============================================================================

DELIMITER //

CREATE TR IF NOT EXISTS audit_users_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (entity_id, action, table_name, record_id, new_values)
    VALUES (NEW.entity_id, 'INSERT', 'users', NEW.id, JSON_OBJECT('entity_id', NEW.entity_id, 'email', NEW.email));
END//

CREATE TR IF NOT EXISTS audit_users_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (entity_id, action, table_name, record_id, old_values, new_values)
    VALUES (NEW.entity_id, 'UPDATE', 'users', NEW.id, 
            JSON_OBJECT('email', OLD.email, 'is_active', OLD.is_active),
            JSON_OBJECT('email', NEW.email, 'is_active', NEW.is_active));
END//

CREATE TR IF NOT EXISTS audit_transactions_insert
AFTER INSERT ON transactions
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (action, table_name, record_id, new_values)
    VALUES ('INSERT', 'transactions', NEW.id, 
            JSON_OBJECT('account_id', NEW.account_id, 'amount', NEW.amount, 'type', NEW.transaction_type));
END//

DELIMITER ;

-- =============================================================================
-- Insert Default Data
-- =============================================================================

-- Create default reputation levels (if not exists)
INSERT INTO reputation (entity_id, score, level, daily_limit, monthly_limit)
VALUES ('system_default', 500, 'silver', 10000.00, 100000.00)
ON DUPLICATE KEY UPDATE score = score;

-- =============================================================================
-- Create Views
-- =============================================================================

CREATE OR REPLACE VIEW v_user_accounts AS
SELECT 
    u.id as user_id,
    u.entity_id,
    u.email,
    a.id as account_id,
    a.account_number,
    a.iban,
    a.account_type,
    a.currency,
    a.balance,
    a.available_balance,
    a.status as account_status,
    r.score as reputation_score,
    r.level as reputation_level
FROM users u
LEFT JOIN accounts a ON u.id = a.user_id
LEFT JOIN reputation r ON u.entity_id = r.entity_id;

CREATE OR REPLACE VIEW v_transaction_summary AS
SELECT 
    a.id as account_id,
    a.account_number,
    COUNT(t.id) as transaction_count,
    SUM(CASE WHEN t.transaction_type IN ('credit', 'transfer') AND t.status = 'completed' THEN t.amount ELSE 0 END) as total_credits,
    SUM(CASE WHEN t.transaction_type IN ('debit', 'sepa') AND t.status = 'completed' THEN t.amount ELSE 0 END) as total_debits,
    MAX(t.created_at) as last_transaction
FROM accounts a
LEFT JOIN transactions t ON a.id = t.account_id
GROUP BY a.id, a.account_number;

-- =============================================================================
-- Grant Permissions
-- =============================================================================

-- Ensure the kiswarm user has all necessary permissions
GRANT ALL PRIVILEGES ON kiswarm6.* TO 'kiswarm'@'%';
FLUSH PRIVILEGES;

-- =============================================================================
-- Complete
-- =============================================================================

SELECT 'KISWARM6.0 Database initialized successfully!' as status;
