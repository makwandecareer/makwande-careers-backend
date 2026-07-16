# Makwande Careers AI CV Builder v4.1

This package completes the next AI CV Builder milestone without changing your existing authentication, employer portal, jobs, applications, or dashboards.

## Added

- ATS assessment history
- Saved AI writing revisions
- Saved generated CV snapshots
- Graduate, Professional, and Executive export templates
- DOCX and PDF export by template
- Safer AI-ready writing service
- Retrieval endpoints for ATS and AI history
- API version 4.1.0

## Installation

Copy everything in this ZIP into:

```text
E:\Makwande_Careers_Backend\makwande-Careers-backend
```

Choose **Replace the files in the destination**.

Then run:

```cmd
cd E:\Makwande_Careers_Backend\makwande-Careers-backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## New and updated endpoints

- `POST /api/ai-cv/generate`
- `POST /api/ai-cv/ats-score`
- `GET /api/ai-cv/ats-history`
- `POST /api/ai-cv/improve-summary`
- `POST /api/ai-cv/improve-experience`
- `GET /api/ai-cv/revisions`
- `GET /api/ai-cv/generated-history`
- `POST /api/ai-cv/export/docx`
- `POST /api/ai-cv/export/pdf`

## Export templates

Use one of:

- `graduate`
- `professional`
- `executive`
- `ats-standard`

## Safety

The service never invents qualifications, employment, metrics, dates, or achievements. Generated wording must be reviewed by the user before publication.
