INSERT OR REPLACE INTO pipeline_sql_audit (script_name, executed_at, note)
VALUES ('03_create_fact_tables.sql', CURRENT_TIMESTAMP, 'Fact tables are created from Pandas model outputs.');

CREATE INDEX IF NOT EXISTS idx_fact_transaction_date ON fact_transaction(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_transaction_customer ON fact_transaction(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_transaction_account ON fact_transaction(account_key);
CREATE INDEX IF NOT EXISTS idx_fact_transaction_category ON fact_transaction(transaction_category_key);
CREATE INDEX IF NOT EXISTS idx_fact_transaction_status ON fact_transaction(transaction_status_key);
