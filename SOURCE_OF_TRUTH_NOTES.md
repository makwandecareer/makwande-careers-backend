# LiveCareer-style profile source of truth

This release changes the candidate profile into the source of truth.

## What changed

- `GET /api/profile` loads saved profile fields.
- `GET /api/profile/source-of-truth` returns one complete career-profile bundle.
- Dashboard completion is calculated by the backend.
- Education, experience, skills, projects, certifications, languages, and references support:
  - create
  - read
  - edit
  - delete
- CV Builder, ATS Analysis, and Career Assistant can use the same profile bundle later without asking users to enter information again.

## Required backend patch

Install the separate backend v6.1 patch before using this frontend.
