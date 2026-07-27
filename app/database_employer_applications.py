from app.database import get_connection


def init_employer_application_database() -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS employer_job_applications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            job_id UUID NOT NULL
                REFERENCES employer_jobs(id)
                ON DELETE CASCADE,

            company_id UUID NOT NULL
                REFERENCES employer_companies(id)
                ON DELETE CASCADE,

            candidate_user_id UUID NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,

            cv_id UUID
                REFERENCES cvs(id)
                ON DELETE SET NULL,

            cover_note TEXT,

            status VARCHAR(30) NOT NULL DEFAULT 'submitted'
                CHECK (
                    status IN (
                        'submitted',
                        'reviewing',
                        'shortlisted',
                        'interview',
                        'offered',
                        'hired',
                        'rejected',
                        'withdrawn'
                    )
                ),

            employer_rating SMALLINT
                CHECK (
                    employer_rating IS NULL
                    OR employer_rating BETWEEN 1 AND 5
                ),

            submitted_at TIMESTAMPTZ
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            last_activity_at TIMESTAMPTZ
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            created_at TIMESTAMPTZ
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMPTZ
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(job_id, candidate_user_id)
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS employer_application_notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            application_id UUID NOT NULL
                REFERENCES employer_job_applications(id)
                ON DELETE CASCADE,

            author_user_id UUID NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,

            note TEXT NOT NULL,

            is_private BOOLEAN NOT NULL DEFAULT TRUE,

            created_at TIMESTAMPTZ
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMPTZ
                NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS employer_application_interviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            application_id UUID NOT NULL
                REFERENCES employer_job_applications(id)
                ON DELETE CASCADE,

            company_id UUID NOT NULL
                REFERENCES employer_companies(id)
                ON DELETE CASCADE,

            candidate_user_id UUID NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,

            scheduled_by UUID NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,

            scheduled_at TIMESTAMPTZ NOT NULL,

            duration_minutes INTEGER NOT NULL DEFAULT 30
                CHECK (duration_minutes BETWEEN 10 AND 480),

            interview_type VARCHAR(40) NOT NULL DEFAULT 'video'
                CHECK (
                    interview_type IN (
                        'video',
                        'phone',
                        'in_person',
                        'assessment'
                    )
                ),

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

            created_at TIMESTAMPTZ
                NOT NULL DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMPTZ
                NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS employer_application_activity (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            application_id UUID NOT NULL
                REFERENCES employer_job_applications(id)
                ON DELETE CASCADE,

            actor_user_id UUID
                REFERENCES users(id)
                ON DELETE SET NULL,

            activity_type VARCHAR(80) NOT NULL,
            from_status VARCHAR(30),
            to_status VARCHAR(30),

            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

            created_at TIMESTAMPTZ
                NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_employer_applications_company
        ON employer_job_applications(company_id, created_at DESC)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_employer_applications_job
        ON employer_job_applications(job_id, created_at DESC)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_employer_applications_candidate
        ON employer_job_applications(candidate_user_id, created_at DESC)
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_employer_applications_status
        ON employer_job_applications(
            company_id,
            status,
            updated_at DESC
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_employer_application_notes
        ON employer_application_notes(
            application_id,
            created_at DESC
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_employer_application_interviews
        ON employer_application_interviews(
            company_id,
            scheduled_at DESC
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_employer_application_activity
        ON employer_application_activity(
            application_id,
            created_at DESC
        )
        """,
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)

        connection.commit()