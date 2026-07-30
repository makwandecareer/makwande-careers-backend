# Makwande Careers CV Export Fix

This patch addresses the two visible failures:

1. Structured API errors are rendered as `[object Object]`.
2. PDF and DOCX export requests fail without producing a downloadable file.

## Frontend changes

- Replace `lib/client-api.ts` with the supplied implementation.
- Add `components/cv-studio/export-document.ts`.
- Apply the edits in `CVStudio.patch.txt`.
- Keep export errors inline; do not replace the whole CV Studio screen.

## Backend changes

The browser screenshot shows HTTP 402 responses from:

- `/api/ai-cv/export/pdf`
- `/api/ai-cv/export/docx`

Locate the dependency or entitlement check that raises 402. Decide whether downloads are:

- authenticated-user features: remove the paid entitlement dependency; or
- paid features: preserve 402 but return a clear string message and ensure the user's active membership is recognised.

The backend must return raw binary bytes with the correct `Content-Type` and `Content-Disposition` headers. Use `backend/export_routes_example.py` as the response contract reference.

## Verification

1. Open CV Studio.
2. Click PDF.
3. Confirm Network shows 200 and `content-type: application/pdf`.
4. Confirm the file downloads and opens.
5. Repeat for DOCX and confirm the Office Open XML MIME type.
6. Test an unauthorised account and verify that a readable message appears without unmounting CV Studio.
