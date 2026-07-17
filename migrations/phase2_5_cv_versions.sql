BEGIN;

CREATE TABLE IF NOT EXISTS cv_versions (
    id UUID PRIMARY KEY,
    cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    title VARCHAR(160) NOT NULL,
    target_role VARCHAR(160),
    template_key VARCHAR(120) NOT NULL,
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cv_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_cv_versions_cv_id
    ON cv_versions (cv_id);

CREATE INDEX IF NOT EXISTS idx_cv_versions_owner_id
    ON cv_versions (owner_id);

ALTER TABLE cvs
    ADD COLUMN IF NOT EXISTS autosave_enabled BOOLEAN NOT NULL DEFAULT TRUE;

COMMIT;
