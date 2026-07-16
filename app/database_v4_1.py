from app.database import get_connection


def init_v4_1_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS ats_assessments (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    cv_id UUID REFERENCES cvs(id) ON DELETE SET NULL,
                    target_role VARCHAR(160),
                    job_description TEXT NOT NULL,
                    score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
                    matched_keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
                    missing_keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
                    recommendations JSONB NOT NULL DEFAULT '[]'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS ai_revisions (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    cv_id UUID REFERENCES cvs(id) ON DELETE SET NULL,
                    revision_type VARCHAR(40) NOT NULL
                        CHECK (revision_type IN ('summary', 'experience')),
                    source_text TEXT NOT NULL,
                    generated_text TEXT NOT NULL,
                    target_role VARCHAR(160),
                    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
                    accepted BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS generated_cv_snapshots (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    cv_id UUID REFERENCES cvs(id) ON DELETE SET NULL,
                    title VARCHAR(200) NOT NULL,
                    target_role VARCHAR(160),
                    template_key VARCHAR(80) NOT NULL,
                    content JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_ats_assessments_user
                    ON ats_assessments(user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_ai_revisions_user
                    ON ai_revisions(user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_generated_snapshots_user
                    ON generated_cv_snapshots(user_id, created_at DESC);
                '''
            )
        connection.commit()
