# Phase 1 completed

This release connects the candidate-facing frontend to the available backend endpoints.

## Live integrations

- `GET /api/users/me`
- `PUT /api/profile`
- `GET/POST /api/education`
- `GET/POST /api/experience`
- `GET/POST /api/skills`
- `GET/POST /api/projects`
- `GET/POST /api/certifications`
- `GET/POST /api/languages`
- `GET/POST /api/references`
- `GET /api/cvs`
- `GET /api/ai-cv/ats-history`

## Current backend limitation

The backend only exposes `PUT /api/profile`. It does not expose `GET /api/profile`,
so the frontend can save profile fields but cannot prefill them after a refresh.
Add a `GET /api/profile` endpoint in a later backend release to resolve that limitation.

The current API also does not expose delete endpoints for education, experience,
skills, projects, certifications, languages, or references. The frontend therefore
supports listing and adding records, but not deleting them.
