from app.database import get_connection


def init_account_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS account_preferences (
                    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    theme VARCHAR(20) NOT NULL DEFAULT 'system',
                    language VARCHAR(10) NOT NULL DEFAULT 'en',
                    timezone VARCHAR(80) NOT NULL DEFAULT 'Africa/Johannesburg',
                    ai_personalisation BOOLEAN NOT NULL DEFAULT TRUE,
                    profile_discoverable BOOLEAN NOT NULL DEFAULT FALSE,
                    product_updates BOOLEAN NOT NULL DEFAULT TRUE,
                    job_alerts BOOLEAN NOT NULL DEFAULT TRUE,
                    application_updates BOOLEAN NOT NULL DEFAULT TRUE,
                    interview_reminders BOOLEAN NOT NULL DEFAULT TRUE,
                    security_alerts BOOLEAN NOT NULL DEFAULT TRUE,
                    email_notifications BOOLEAN NOT NULL DEFAULT TRUE,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS user_sessions (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_jti UUID UNIQUE NOT NULL,
                    user_agent TEXT,
                    ip_address VARCHAR(80),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    revoked_at TIMESTAMPTZ
                );

                CREATE TABLE IF NOT EXISTS security_events (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    event_type VARCHAR(80) NOT NULL,
                    ip_address VARCHAR(80),
                    user_agent TEXT,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_user_sessions_active
                    ON user_sessions(user_id, revoked_at, expires_at DESC);
                CREATE INDEX IF NOT EXISTS idx_security_events_user
                    ON security_events(user_id, created_at DESC);
                """
            )
        connection.commit()
