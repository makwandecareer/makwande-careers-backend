BEGIN;

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    plan_code VARCHAR(50) NOT NULL,
    amount INTEGER NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'ZAR',

    status VARCHAR(30) NOT NULL DEFAULT 'inactive',

    starts_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT subscriptions_amount_positive
        CHECK (amount > 0),

    CONSTRAINT subscriptions_status_valid
        CHECK (
            status IN (
                'inactive',
                'active',
                'expired',
                'cancelled'
            )
        ),

    CONSTRAINT subscriptions_plan_valid
        CHECK (
            plan_code IN (
                'trial_14_day',
                'premium_30_day'
            )
        )
);

CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,

    reference VARCHAR(150) NOT NULL UNIQUE,
    paystack_access_code VARCHAR(150),

    plan_code VARCHAR(50) NOT NULL,
    amount INTEGER NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'ZAR',

    status VARCHAR(30) NOT NULL DEFAULT 'pending',

    paystack_transaction_id VARCHAR(100),
    paystack_channel VARCHAR(50),
    customer_email VARCHAR(320),

    paid_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,

    raw_response JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT payment_transactions_amount_positive
        CHECK (amount > 0),

    CONSTRAINT payment_transactions_status_valid
        CHECK (
            status IN (
                'pending',
                'success',
                'failed',
                'abandoned',
                'reversed'
            )
        ),

    CONSTRAINT payment_transactions_plan_valid
        CHECK (
            plan_code IN (
                'trial_14_day',
                'premium_30_day'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id
    ON subscriptions(user_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status
    ON subscriptions(user_id, status);

CREATE INDEX IF NOT EXISTS idx_subscriptions_expires_at
    ON subscriptions(expires_at);

CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id
    ON payment_transactions(user_id);

CREATE INDEX IF NOT EXISTS idx_payment_transactions_reference
    ON payment_transactions(reference);

CREATE INDEX IF NOT EXISTS idx_payment_transactions_status
    ON payment_transactions(status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_subscription_per_user
    ON subscriptions(user_id)
    WHERE status = 'active';

COMMIT;