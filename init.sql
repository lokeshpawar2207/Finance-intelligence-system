-- Bluestock Data Warehouse - Star Schema
-- PostgreSQL 15
-- Run this file during Docker initialization

-- ============================================
-- DIMENSION TABLES
-- ============================================

CREATE TABLE dim_sector (
    sector_id SERIAL PRIMARY KEY,
    sector_name VARCHAR(100) NOT NULL UNIQUE,
    sector_code VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_health_label (
    label_id SERIAL PRIMARY KEY,
    label_name VARCHAR(50) NOT NULL UNIQUE,
    min_score NUMERIC(5,2),
    max_score NUMERIC(5,2),
    color_hex VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_company (
    symbol VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    sector_id INT REFERENCES dim_sector(sector_id),
    sub_sector VARCHAR(100),
    company_logo TEXT,
    website VARCHAR(255),
    nse_url VARCHAR(255),
    bse_url VARCHAR(255),
    face_value NUMERIC(10,2),
    book_value NUMERIC(15,2),
    about_company TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_year (
    year_id SERIAL PRIMARY KEY,
    year_label VARCHAR(20) NOT NULL UNIQUE,
    fiscal_year INT,
    quarter VARCHAR(5),
    is_ttm BOOLEAN DEFAULT FALSE,
    is_half_year BOOLEAN DEFAULT FALSE,
    sort_order INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FACT TABLES
-- ============================================

CREATE TABLE fact_profit_loss (
    pl_id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
    year_id INT NOT NULL REFERENCES dim_year(year_id),
    sales NUMERIC(20,2),
    expenses NUMERIC(20,2),
    operating_profit NUMERIC(20,2),
    opm_pct NUMERIC(7,2),
    other_income NUMERIC(20,2),
    interest NUMERIC(20,2),
    depreciation NUMERIC(20,2),
    profit_before_tax NUMERIC(20,2),
    tax_pct NUMERIC(7,2),
    net_profit NUMERIC(20,2),
    eps NUMERIC(15,2),
    dividend_payout_pct NUMERIC(7,2),
    net_profit_margin_pct NUMERIC(7,2),
    expense_ratio_pct NUMERIC(7,2),
    interest_coverage NUMERIC(15,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, year_id)
);

CREATE TABLE fact_balance_sheet (
    bs_id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
    year_id INT NOT NULL REFERENCES dim_year(year_id),
    equity_capital NUMERIC(20,2),
    reserves NUMERIC(20,2),
    borrowings NUMERIC(20,2),
    other_liabilities NUMERIC(20,2),
    total_liabilities NUMERIC(20,2),
    fixed_assets NUMERIC(20,2),
    cwip NUMERIC(20,2),
    investments NUMERIC(20,2),
    other_assets NUMERIC(20,2),
    total_assets NUMERIC(20,2),
    debt_to_equity NUMERIC(15,4),
    equity_ratio NUMERIC(7,4),
    book_value_per_share NUMERIC(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, year_id)
);

CREATE TABLE fact_cash_flow (
    cf_id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
    year_id INT NOT NULL REFERENCES dim_year(year_id),
    operating_activity NUMERIC(20,2),
    investing_activity NUMERIC(20,2),
    financing_activity NUMERIC(20,2),
    net_cash_flow NUMERIC(20,2),
    free_cash_flow NUMERIC(20,2),
    cash_conversion_ratio NUMERIC(7,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, year_id)
);

CREATE TABLE fact_analysis (
    analysis_id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
    period_label VARCHAR(20) NOT NULL,
    compounded_sales_growth_pct NUMERIC(7,2),
    compounded_profit_growth_pct NUMERIC(7,2),
    stock_price_cagr_pct NUMERIC(7,2),
    roe_pct NUMERIC(7,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, period_label)
);

CREATE TABLE fact_ml_scores (
    score_id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_score NUMERIC(5,2),
    profitability_score NUMERIC(5,2),
    growth_score NUMERIC(5,2),
    leverage_score NUMERIC(5,2),
    cashflow_score NUMERIC(5,2),
    dividend_score NUMERIC(5,2),
    trend_score NUMERIC(5,2),
    health_label_id INT REFERENCES dim_health_label(label_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fact_pros_cons (
    insight_id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
    is_pro BOOLEAN NOT NULL,
    category VARCHAR(100),
    text TEXT NOT NULL,
    source VARCHAR(50),
    confidence NUMERIC(5,2),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX idx_fact_pl_symbol ON fact_profit_loss(symbol);
CREATE INDEX idx_fact_pl_year ON fact_profit_loss(year_id);
CREATE INDEX idx_fact_bs_symbol ON fact_balance_sheet(symbol);
CREATE INDEX idx_fact_bs_year ON fact_balance_sheet(year_id);
CREATE INDEX idx_fact_cf_symbol ON fact_cash_flow(symbol);
CREATE INDEX idx_fact_cf_year ON fact_cash_flow(year_id);
CREATE INDEX idx_fact_analysis_symbol ON fact_analysis(symbol);
CREATE INDEX idx_fact_ml_scores_symbol ON fact_ml_scores(symbol);
CREATE INDEX idx_fact_pros_cons_symbol ON fact_pros_cons(symbol);

-- ============================================
-- SEED DATA - HEALTH LABELS
-- ============================================

INSERT INTO dim_health_label (label_name, min_score, max_score, color_hex) VALUES
('EXCELLENT', 85.00, 100.00, '#00AA00'),
('GOOD', 70.00, 84.99, '#90EE90'),
('AVERAGE', 50.00, 69.99, '#FFFF00'),
('WEAK', 35.00, 49.99, '#FFA500'),
('POOR', 0.00, 34.99, '#FF0000');

-- ============================================
-- SEED DATA - SECTORS
-- ============================================

INSERT INTO dim_sector (sector_name, sector_code, description) VALUES
('IT Services', 'IT', 'Information Technology Services'),
('Banking', 'BANK', 'Banking & Financial Services'),
('NBFC', 'NBFC', 'Non-Banking Financial Companies'),
('Insurance', 'INS', 'Insurance Companies'),
('Energy', 'ENERGY', 'Energy & Power Generation'),
('Power', 'POWER', 'Power Distribution & Utilities'),
('Ports', 'PORTS', 'Port & Logistics'),
('Cement', 'CEMENT', 'Cement Manufacturing'),
('Healthcare', 'HEALTH', 'Healthcare & Pharmaceuticals'),
('Auto', 'AUTO', 'Automobile & Auto Components'),
('Paint', 'PAINT', 'Paint & Coatings'),
('Consumer Goods', 'FMCG', 'FMCG & Consumer Goods'),
('Holding Company', 'HOLDING', 'Holding & Investment Companies'),
('Telecom', 'TELECOM', 'Telecom & Communications'),
('Real Estate', 'REALESTATE', 'Real Estate & Construction');
