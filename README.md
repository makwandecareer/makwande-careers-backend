# Makwande Careers Backend Database Refactor

This patch safely consolidates the following active database initialisers:

- `app/database_v4.py`
- `app/database_v4_1.py`
- `app/database_v5.py`

into:

- `app/database_features.py`

No table, column, constraint, index, or CV-template seed record has been removed.

## Files to copy

1. Copy `app/database_features.py` into your backend repository.
2. Replace `app/main.py` with the supplied `app/main.py`.

## Files to delete only after testing

- `app/database_v4.py`
- `app/database_v4_1.py`
- `app/database_v5.py`

## Safe Git commands

```bash
git checkout -b refactor/consolidate-database-initializers

# Copy the supplied files into the repository first.

python -m compileall app

# Start the API and confirm database initialisation succeeds.
uvicorn app.main:app --reload

# Check these endpoints:
# GET /
# GET /health
# GET /docs

git add app/database_features.py app/main.py
git commit -m "Consolidate versioned database initializers"

# Only after the application starts successfully:
git rm app/database_v4.py app/database_v4_1.py app/database_v5.py
git commit -m "Remove replaced versioned database initializer files"

git push -u origin refactor/consolidate-database-initializers
```

## Production checks before merging

Confirm that these tables still exist:

- certifications
- projects
- languages
- candidate_references
- cv_templates
- employers
- jobs
- applications
- shortlists
- ats_assessments
- ai_revisions
- generated_cv_snapshots
- saved_jobs
- candidate_invitations
- interviews
- notifications
- audit_logs

Do not drop any database tables. This refactor changes only Python initialisation files.
