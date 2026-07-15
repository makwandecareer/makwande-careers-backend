# Makwande Careers AI CV Builder v3

Copy these files into your existing backend project and replace files when prompted.

Install:

```cmd
python -m pip install -r requirements.txt
```

Run:

```cmd
python -m uvicorn app.main:app --reload
```

New endpoints:

- POST /api/ai-cv/generate
- POST /api/ai-cv/ats-score
- POST /api/ai-cv/improve-summary
- POST /api/ai-cv/improve-experience
- POST /api/ai-cv/export/docx
- POST /api/ai-cv/export/pdf
