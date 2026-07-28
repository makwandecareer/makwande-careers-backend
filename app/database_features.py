from app.database import get_connection


def init_feature_database() -> None:
    """
    Initialise feature tables introduced across the former v4, v4.1 and v5
    database modules.

    This function is intentionally idempotent. It preserves every table,
    constraint, index and seed record from:
      - app/database_v4.py
      - app/database_v4_1.py
      - app/database_v5.py
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS certifications (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(240) NOT NULL,
                    issuer VARCHAR(240),
                    issue_date DATE,
                    expiry_date DATE,
                    credential_id VARCHAR(160),
                    credential_url TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(240) NOT NULL,
                    description TEXT,
                    project_url TEXT,
                    technologies JSONB NOT NULL DEFAULT '[]'::jsonb,
                    start_date DATE,
                    end_date DATE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS languages (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(120) NOT NULL,
                    proficiency VARCHAR(80),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, name)
                );

                CREATE TABLE IF NOT EXISTS candidate_references (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    full_name VARCHAR(200) NOT NULL,
                    relationship VARCHAR(160),
                    company VARCHAR(240),
                    email VARCHAR(320),
                    phone VARCHAR(40),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS cv_templates (
                    id UUID PRIMARY KEY,
                    template_key VARCHAR(80) NOT NULL UNIQUE,
                    name VARCHAR(160) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS employers (
                    id UUID PRIMARY KEY,
                    owner_user_id UUID NOT NULL UNIQUE
                        REFERENCES users(id) ON DELETE CASCADE,
                    company_name VARCHAR(240) NOT NULL,
                    website_url TEXT,
                    industry VARCHAR(160),
                    location VARCHAR(200),
                    description TEXT,
                    verified BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id UUID PRIMARY KEY,
                    employer_id UUID NOT NULL
                        REFERENCES employers(id) ON DELETE CASCADE,
                    title VARCHAR(240) NOT NULL,
                    location VARCHAR(200),
                    employment_type VARCHAR(80),
                    workplace_type VARCHAR(80),
                    description TEXT NOT NULL,
                    requirements JSONB NOT NULL DEFAULT '[]'::jsonb,
                    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
                    closing_date DATE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id UUID PRIMARY KEY,
                    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    candidate_user_id UUID NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
                    cover_note TEXT,
                    status VARCHAR(30) NOT NULL DEFAULT 'submitted'
                        CHECK (
                            status IN (
                                'submitted',
                                'reviewing',
                                'shortlisted',
                                'interview',
                                'rejected',
                                'withdrawn',
                                'hired'
                            )
                        ),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(job_id, candidate_user_id)
                );

                CREATE TABLE IF NOT EXISTS shortlists (
                    id UUID PRIMARY KEY,
                    employer_id UUID NOT NULL
                        REFERENCES employers(id) ON DELETE CASCADE,
                    candidate_user_id UUID NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
                    notes TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(employer_id, candidate_user_id, job_id)
                );

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

                CREATE TABLE IF NOT EXISTS saved_jobs (
                    id UUID PRIMARY KEY,
                    candidate_user_id UUID NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(candidate_user_id, job_id)
                );

                CREATE TABLE IF NOT EXISTS candidate_invitations (
                    id UUID PRIMARY KEY,
                    employer_id UUID NOT NULL
                        REFERENCES employers(id) ON DELETE CASCADE,
                    candidate_user_id UUID NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
                    message TEXT,
                    status VARCHAR(30) NOT NULL DEFAULT 'pending'
                        CHECK (
                            status IN (
                                'pending',
                                'accepted',
                                'declined',
                                'expired'
                            )
                        ),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS interviews (
                    id UUID PRIMARY KEY,
                    application_id UUID
                        REFERENCES applications(id) ON DELETE SET NULL,
                    employer_id UUID NOT NULL
                        REFERENCES employers(id) ON DELETE CASCADE,
                    candidate_user_id UUID NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
                    scheduled_at TIMESTAMPTZ NOT NULL,
                    duration_minutes INTEGER NOT NULL DEFAULT 30
                        CHECK (duration_minutes BETWEEN 10 AND 480),
                    meeting_url TEXT,
                    location VARCHAR(300),
                    notes TEXT,
                    status VARCHAR(30) NOT NULL DEFAULT 'scheduled'
                        CHECK (
                            status IN (
                                'scheduled',
                                'completed',
                                'cancelled',
                                'rescheduled',
                                'no_show'
                            )
                        ),
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

                CREATE INDEX IF NOT EXISTS idx_certifications_user_id
                    ON certifications(user_id);

                CREATE INDEX IF NOT EXISTS idx_projects_user_id
                    ON projects(user_id);

                CREATE INDEX IF NOT EXISTS idx_languages_user_id
                    ON languages(user_id);

                CREATE INDEX IF NOT EXISTS idx_references_user_id
                    ON candidate_references(user_id);

                CREATE INDEX IF NOT EXISTS idx_jobs_employer_id
                    ON jobs(employer_id);

                CREATE INDEX IF NOT EXISTS idx_jobs_active
                    ON jobs(is_active);

                CREATE INDEX IF NOT EXISTS idx_applications_candidate
                    ON applications(candidate_user_id);

                CREATE INDEX IF NOT EXISTS idx_applications_job
                    ON applications(job_id);

                CREATE INDEX IF NOT EXISTS idx_ats_assessments_user
                    ON ats_assessments(user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_ai_revisions_user
                    ON ai_revisions(user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_generated_snapshots_user
                    ON generated_cv_snapshots(user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_saved_jobs_candidate
                    ON saved_jobs(candidate_user_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_invitations_candidate
                    ON candidate_invitations(
                        candidate_user_id,
                        created_at DESC
                    );

                CREATE INDEX IF NOT EXISTS idx_invitations_employer
                    ON candidate_invitations(
                        employer_id,
                        created_at DESC
                    );

                CREATE INDEX IF NOT EXISTS idx_interviews_candidate
                    ON interviews(candidate_user_id, scheduled_at);

                CREATE INDEX IF NOT EXISTS idx_interviews_employer
                    ON interviews(employer_id, scheduled_at);

                CREATE INDEX IF NOT EXISTS idx_notifications_user
                    ON notifications(user_id, is_read, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_audit_logs_created
                    ON audit_logs(created_at DESC);

                INSERT INTO cv_templates (
                    id,
                    template_key,
                    name,
                    description,
                    is_active
                )
                VALUES
                    (
                        gen_random_uuid(),
                        'ats-standard',
                        'ATS Standard',
                        'Clean ATS-friendly template.',
                        TRUE
                    ),
                    (
                        gen_random_uuid(),
                        'graduate',
                        'Graduate',
                        'Graduate and entry-level template.',
                        TRUE
                    ),
                    (
                        gen_random_uuid(),
                        'executive',
                        'Executive',
                        'Senior and executive template.',
                        TRUE
                    )
                ON CONFLICT (template_key) DO NOTHING;
                """
            )

        connection.commit()
