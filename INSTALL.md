# Phase 2.5 Installation

## 1. PostgreSQL

Run:

```sql
\i backend/migrations/phase2_5_cv_versions.sql
```

or paste the SQL into the same `psql` database used by Makwande Careers.

## 2. Backend

Copy:

```text
backend/app/routes/cv_versions.py
backend/app/schemas/cv_versions.py
```

into the matching backend folders.

Add to `app/main.py`:

```python
from app.routes import cv_versions
app.include_router(cv_versions.router, prefix="/api")
```

Do not register the old CV CRUD router at the same paths if it already defines
`/api/cvs`. Replace or disable duplicate route definitions.

Restart the backend.

## 3. Frontend

Extract:

```text
frontend/Makwande_Careers_Frontend_v14_Backend_Autosave.zip
```

as the frontend project.

The package adds backend API functions and an autosave hook without changing
the current visual layout.

To enable the hook in `CVStudio.tsx`, add:

```tsx
import { useCVBackendAutosave } from "@/hooks/use-cv-backend-autosave";
```

Inside the component, after the draft state:

```tsx
const {
  backendSaveState,
  backendSaveError,
} = useCVBackendAutosave(draft);
```

You may display the state in the existing toolbar later, but this is optional.
The autosave process works without adding new visual elements.
