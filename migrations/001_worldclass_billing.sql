CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS billing_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    amount_subunits INTEGER NOT NULL CHECK (amount_subunits > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    access_days INTEGER NOT NULL CHECK (access_days > 0),
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    paystack_plan_code VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS billing_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(320) NOT NULL,
    paystack_customer_code VARCHAR(100) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS billing_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    plan_code VARCHAR(50) NOT NULL,
    status VARCHAR(40) NOT NULL,
    paystack_customer_code VARCHAR(100),
    paystack_subscription_code VARCHAR(100) UNIQUE,
    paystack_email_token VARCHAR(200),
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    cancelled_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_billing_subscription_user ON billing_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS ix_billing_subscription_end ON billing_subscriptions(current_period_end);
CREATE INDEX IF NOT EXISTS ix_billing_subscription_status ON billing_subscriptions(status);

CREATE TABLE IF NOT EXISTS billing_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    plan_code VARCHAR(50) NOT NULL,
    reference VARCHAR(120) UNIQUE NOT NULL,
    paystack_transaction_id VARCHAR(100) UNIQUE,
    amount_subunits INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(40) NOT NULL,
    channel VARCHAR(40),
    authorization_last4 VARCHAR(4),
    authorization_brand VARCHAR(50),
    paid_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,
    gateway_response JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_billing_payment_user ON billing_payments(user_id);
CREATE INDEX IF NOT EXISTS ix_billing_payment_status ON billing_payments(status);

CREATE TABLE IF NOT EXISTS billing_webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_key VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    processing_error TEXT,
    received_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_billing_webhook_type ON billing_webhook_events(event_type);

CREATE TABLE IF NOT EXISTS billing_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(120),
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_billing_audit_user ON billing_audit_logs(user_id);
