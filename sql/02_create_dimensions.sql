INSERT OR REPLACE INTO pipeline_sql_audit (script_name, executed_at, note)
VALUES ('02_create_dimensions.sql', CURRENT_TIMESTAMP, 'Dimension tables are created from Pandas model outputs.');

CREATE INDEX IF NOT EXISTS idx_dim_customer_business_key ON dim_customer(customer_id);
CREATE INDEX IF NOT EXISTS idx_dim_account_business_key ON dim_account(account_id);
CREATE INDEX IF NOT EXISTS idx_dim_merchant_business_key ON dim_merchant(merchant_id);
CREATE INDEX IF NOT EXISTS idx_dim_date_date_key ON dim_date(date_key);
CREATE INDEX IF NOT EXISTS idx_dim_category_name ON dim_transaction_category(transaction_category);
