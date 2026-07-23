from app.database import get_connection


def init_employer_database() -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS employer_companies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
            name VARCHAR(180) NOT NULL,
            registration_number VARCHAR(100),
            industry VARCHAR(120),
            company_size VARCHAR(50),
            website VARCHAR(255),
            phone VARCHAR(50),
            email VARCHAR(255),
            location VARCHAR(255),
            description TEXT,
            verification_status VARCHAR(30) NOT NULL DEFAULT 'unverified',
            hiring_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS employer_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES employer_companies(id) ON DELETE CASCADE,
            created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(180) NOT NULL,
            department VARCHAR(120),
            location VARCHAR(255),
            workplace_type VARCHAR(30) NOT NULL DEFAULT 'onsite',
            employment_type VARCHAR(40) NOT NULL DEFAULT 'full_time',
            seniority_level VARCHAR(60),
            salary_min NUMERIC(14,2),
            salary_max NUMERIC(14,2),
            salary_currency VARCHAR(10) NOT NULL DEFAULT 'ZAR',
            salary_visible BOOLEAN NOT NULL DEFAULT FALSE,
            summary TEXT,
            responsibilities TEXT[] NOT NULL DEFAULT '{}',
            requirements TEXT[] NOT NULL DEFAULT '{}',
            skills TEXT[] NOT NULL DEFAULT '{}',
            benefits TEXT[] NOT NULL DEFAULT '{}',
            screening_questions JSONB NOT NULL DEFAULT '[]'::jsonb,
            closing_date DATE,
            status VARCHAR(30) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_employer_jobs_company ON employer_jobs(company_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_employer_jobs_status ON employer_jobs(status, closing_date)",
    ]
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
            for statement in statements:
                cursor.execute(statement)
        connection.commit()
