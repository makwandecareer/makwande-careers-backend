# Phase 2 — Global-standard Professional CV Builder

This release upgrades the existing AI CV Builder into a professional, source-of-truth CV workflow.

## Included

- Automatic loading from `/api/profile/source-of-truth`
- Profile-readiness indicator
- Target-role customisation
- Four professional templates
- Live A4-style CV preview
- Generate and save using `POST /api/ai-cv/generate`
- PDF export using `POST /api/ai-cv/export/pdf`
- DOCX export using `POST /api/ai-cv/export/docx`
- Improved My CVs document library
- Responsive desktop, tablet and mobile layouts
- No repeated entry of Profile, Education, Experience, Skills, Projects, Certifications, Languages or References

## Install

Replace your current frontend folder with this release, retain your `.env.local`, then run:

```cmd
cd /d E:\Makwande_Careers_Frontend
npm install
npm run dev
```

Required local environment:

```env
BACKEND_API_URL=http://127.0.0.1:8000
```

Keep the FastAPI backend running on port 8000.
