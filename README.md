# Makwande Careers AI Career Engine v1

Backend patch for FastAPI using the OpenAI Responses API and structured outputs.

## Features

- Career roadmap generation
- Skills-gap analysis
- Interview preparation
- Cover-letter generation
- Professional-summary improvement
- Experience rewriting
- Job-match analysis
- Structured JSON responses
- Uses the authenticated user's source-of-truth profile
- OpenAI API key remains server-side

## Install

1. Copy the supplied `app` folder into the backend project.
2. Add `openai>=2.0.0` to `requirements.txt`.
3. Add these environment variables:

```env
OPENAI_API_KEY=your-secret-key
OPENAI_MODEL=gpt-5.4-mini
```

4. In `app/main.py` add:

```python
from app.routes import ai_career_engine
app.include_router(ai_career_engine.router, prefix="/api")
```

5. Restart the backend.

## Endpoints

- `POST /api/ai-career/roadmap`
- `POST /api/ai-career/skills-gap`
- `POST /api/ai-career/interview-prep`
- `POST /api/ai-career/cover-letter`
- `POST /api/ai-career/improve-summary`
- `POST /api/ai-career/improve-experience`
- `POST /api/ai-career/job-match`
