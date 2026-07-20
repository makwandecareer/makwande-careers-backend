# Backend fixes applied

- Registered the existing AI Career Engine router in `app/main.py`.
- Added `openai>=2.0,<3` to `requirements.txt`.
- Added OpenAI and Paystack configuration placeholders to `.env.example`.
- Added `app/routes/openai_career.py` as a compatibility import for older deployments.
- Added `app/integrations/router.py` and registered `/api/integrations/status`.
- Fixed the schema import conflict caused by having both `app/schemas.py` and an
  `app/schemas/` directory by adding `app/schemas_ai_career.py` and updating the
  AI Career Engine import.
- Verified that all seven `/api/ai-career/*` endpoints and the integrations
  status endpoint register successfully.

## Before starting

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and provide real values for at least:

```env
JWT_SECRET=...
DATABASE_URL=...
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.4-mini
```

Then run:

```bash
uvicorn app.main:app --reload
```
