from contextlib import contextmanager
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from app.config import settings

pool = ConnectionPool(settings.database_url, min_size=1, max_size=5, kwargs={'row_factory': dict_row}, open=False)

def open_pool():
    pool.open(); pool.wait()

def close_pool():
    pool.close()

@contextmanager
def get_connection():
    with pool.connection() as conn:
        yield conn

def init_database():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
              id UUID PRIMARY KEY, email VARCHAR(320) UNIQUE NOT NULL,
              full_name VARCHAR(200) NOT NULL, password_hash VARCHAR(255) NOT NULL,
              role VARCHAR(30) NOT NULL DEFAULT 'candidate', is_active BOOLEAN NOT NULL DEFAULT TRUE,
              created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS profiles (
              id UUID PRIMARY KEY, user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              phone VARCHAR(40), location VARCHAR(200), professional_title VARCHAR(160),
              professional_summary TEXT, linkedin_url TEXT, portfolio_url TEXT,
              visibility VARCHAR(20) NOT NULL DEFAULT 'private', updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS education (
              id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              institution VARCHAR(240) NOT NULL, qualification VARCHAR(240) NOT NULL,
              field_of_study VARCHAR(240), start_date DATE, end_date DATE, description TEXT
            );
            CREATE TABLE IF NOT EXISTS experience (
              id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              company VARCHAR(240) NOT NULL, job_title VARCHAR(200) NOT NULL,
              start_date DATE, end_date DATE, description TEXT, achievements JSONB NOT NULL DEFAULT '[]'::jsonb
            );
            CREATE TABLE IF NOT EXISTS skills (
              id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              name VARCHAR(160) NOT NULL, proficiency VARCHAR(40), UNIQUE(user_id,name)
            );
            CREATE TABLE IF NOT EXISTS cvs (
              id UUID PRIMARY KEY, owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              title VARCHAR(160) NOT NULL, target_role VARCHAR(160), template_key VARCHAR(80) NOT NULL DEFAULT 'ats-standard',
              content JSONB NOT NULL DEFAULT '{}'::jsonb, is_public_to_employers BOOLEAN NOT NULL DEFAULT FALSE,
              version INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS employers (
              id UUID PRIMARY KEY, owner_user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              company_name VARCHAR(240) NOT NULL, website_url TEXT, industry VARCHAR(160), location VARCHAR(200), verified BOOLEAN NOT NULL DEFAULT FALSE
            );
            CREATE TABLE IF NOT EXISTS payment_transactions (
              reference VARCHAR(160) PRIMARY KEY,
              user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              email VARCHAR(320) NOT NULL,
              plan_key VARCHAR(80) NOT NULL,
              expected_amount INTEGER NOT NULL,
              currency VARCHAR(10) NOT NULL DEFAULT 'ZAR',
              status VARCHAR(40) NOT NULL DEFAULT 'pending',
              paystack_transaction_id BIGINT,
              paid_at TIMESTAMPTZ,
              raw_event JSONB,
              created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS subscriptions (
              user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
              plan_key VARCHAR(80) NOT NULL,
              status VARCHAR(30) NOT NULL DEFAULT 'active',
              starts_at TIMESTAMPTZ NOT NULL,
              expires_at TIMESTAMPTZ NOT NULL,
              payment_reference VARCHAR(160) UNIQUE NOT NULL REFERENCES payment_transactions(reference),
              updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_cvs_owner ON cvs(owner_id);
            CREATE INDEX IF NOT EXISTS idx_cvs_public ON cvs(is_public_to_employers);
            CREATE INDEX IF NOT EXISTS idx_payment_transactions_user ON payment_transactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON payment_transactions(status);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_expiry ON subscriptions(expires_at);
            ''')
        conn.commit()
