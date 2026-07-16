# Makwande Careers Backend v6 Final

Backend-only release. No frontend files are included.

## Adds

- Candidate dashboard summary
- Employer dashboard summary
- Employer candidate search
- AI job matching
- Cover-letter generation
- Interview preparation
- Skills-gap analysis
- Career-roadmap generation
- API version 6.0.0

## Install

Copy everything in this package into:

```text
E:\Makwande_Careers_Backend\makwande-Careers-backend
```

Choose **Replace the files in the destination**.

Run:

```cmd
cd E:\Makwande_Careers_Backend\makwande-Careers-backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## New endpoints

- `GET /api/dashboard/candidate-v6`
- `GET /api/dashboard/employer-v6`
- `GET /api/employer/candidate-search-v6`
- `POST /api/ai-recruiter/job-match`
- `POST /api/career/cover-letter-v6`
- `POST /api/career/interview-prep-v6`
- `POST /api/career/skills-gap-v6`
- `POST /api/career/roadmap-v6`
