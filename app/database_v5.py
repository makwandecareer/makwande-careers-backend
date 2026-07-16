from app.database import get_connection


def init_v5_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS saved_jobs (
                    id UUID PRIMARY KEY,
                    candidate_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(candidate_user_id, job_id)
                );

                CREATE TABLE IF NOT EXISTS candidate_invitations (
                    id UUID PRIMARY KEY,
                    employer_id UUID NOT NULL REFERENCES employers(id) ON DELETE CASCADE,
                    candidate_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
                    message TEXT,
                    status VARCHAR(30) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','accepted','declined','expired')),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS interviews (
                    id UUID PRIMARY KEY,
                    application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
                    employer_id UUID NOT NULL REFERENCES employers(id) ON DELETE CASCADE,
                    candidate_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
                    scheduled_at TIMESTAMPTZ NOT NULL,
                    duration_minutes INTEGER NOT NULL DEFAULT 30
                        CHECK (duration_minutes BETWEEN 10 AND 480),
                    meeting_url TEXT,
                    location VARCHAR(300),
                    notes TEXT,
                    status VARCHAR(30) NOT NULL DEFAULT 'scheduled'
                        CHECK (status IN ('scheduled','completed','cancelled','rescheduled','no_show')),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    notification_type VARCHAR(80) NOT NULL,
                    title VARCHAR(240) NOT NULL,
                    message TEXT NOT NULL,
                    action_url TEXT,
                    is_read BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id UUID PRIMARY KEY,
                    actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    action VARCHAR(160) NOT NULL,
                    entity_type VARCHAR(80),
                    entity_id UUID,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_saved_jobs_candidate
                    ON saved_jobs(candidate_user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_invitations_candidate
                    ON candidate_invitations(candidate_user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_invitations_employer
                    ON candidate_invitations(employer_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_interviews_candidate
                    ON interviews(candidate_user_id, scheduled_at);

                CREATE INDEX IF NOT EXISTS idx_interviews_employer
                    ON interviews(employer_id, scheduled_at);

                CREATE INDEX IF NOT EXISTS idx_notifications_user
                    ON notifications(user_id, is_read, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_audit_logs_created
                    ON audit_logs(created_at DESC);
                '''
            )
        connection.commit()
