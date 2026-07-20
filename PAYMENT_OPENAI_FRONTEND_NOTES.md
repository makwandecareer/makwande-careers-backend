# Frontend integration contract

- OpenAI model: `gpt-5.4-mini`
- Trial: R45 / 14 days (`4500` cents)
- Premium: R300 / 30 days (`30000` cents)
- Frontend callback: `/payment/callback`
- Billing endpoints: `/api/billing/plans`, `/api/billing/initialize`, `/api/billing/verify/{reference}`
- OpenAI endpoints: `/api/ai-career/*`

## Paystack webhook

The backend now exposes `POST /api/billing/webhook`.

Set the Paystack webhook URL to:

`https://YOUR-PUBLIC-BACKEND-DOMAIN/api/billing/webhook`

The endpoint validates `x-paystack-signature` with HMAC-SHA512, returns quickly,
verifies successful charges server-side, checks amount/currency, and idempotently
activates or extends the user's access period.

Use `GET /api/billing/subscription` (authenticated) to read current access.
`localhost` cannot receive Paystack webhook requests; use a deployed HTTPS backend
or a secure tunnel for test-mode development.
