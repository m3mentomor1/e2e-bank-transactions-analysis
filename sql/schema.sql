-- PostgreSQL schema for processed bank transactions
-- Source: data/processed/bank_transactions_cleaned.csv

DROP TABLE IF EXISTS bank_transactions CASCADE;

CREATE TABLE bank_transactions (
    transaction_number INTEGER NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    transaction_description VARCHAR(32) NOT NULL,
    transaction_direction VARCHAR(10) NOT NULL,
    debit_amount NUMERIC(12, 2) NOT NULL,
    credit_amount NUMERIC(12, 2) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    abs_amount NUMERIC(12, 2) NOT NULL,
    balance NUMERIC(12, 2) NOT NULL,
    category VARCHAR(64) NOT NULL,
    location_city VARCHAR(32) NOT NULL,
    location_country VARCHAR(32) NOT NULL,
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    year_month CHAR(7) NOT NULL,
    day_of_week VARCHAR(12) NOT NULL,
    PRIMARY KEY (transaction_number)
);

CREATE INDEX idx_bank_transactions_date ON bank_transactions (transaction_date);
CREATE INDEX idx_bank_transactions_category ON bank_transactions (category);
CREATE INDEX idx_bank_transactions_city ON bank_transactions (location_city);
CREATE INDEX idx_bank_transactions_year_month ON bank_transactions (year_month);
CREATE INDEX idx_bank_transactions_direction ON bank_transactions (transaction_direction);
