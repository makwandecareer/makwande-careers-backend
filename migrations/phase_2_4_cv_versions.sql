CREATE TABLE IF NOT EXISTS cv_versions (
    id UUID PRIMARY KEY,
    cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    title VARCHAR(160) NOT NULL,
    target_role VARCHAR(160),
    template_key VARCHAR(80) NOT NULL DEFAULT 'ats-standard',
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cv_id, version)
);

CREATE INDEX IF NOT EXISTS idx_cv_versions_cv_id
ON cv_versions(cv_id, version DESC);

CREATE INDEX IF NOT EXISTS idx_cv_versions_owner_id
ON cv_versions(owner_id, created_at DESC);
