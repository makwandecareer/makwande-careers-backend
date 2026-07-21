# OpenAI and Paystack frontend

## Environment

Create `.env.local`:

```env
BACKEND_API_URL=http://127.0.0.1:8000
```

Restart Next.js after changing environment variables.

## Implemented flows

- AI Career Engine with roadmap, skills gap, interview preparation, cover letter, summary improvement, experience improvement and job matching.
- Authenticated requests are sent through `/api/backend/*`; the access token stays in the secure HTTP-only cookie.
- Billing page at `/dashboard/billing`.
- Paystack checkout initialization and redirect.
- Callback verification at `/payment/callback`.
- Plans: R45 for 14 days and R300 for 30 days.

## Run

```bash
npm install
npm run dev
```
