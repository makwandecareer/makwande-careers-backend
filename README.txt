MAKWANDE CAREERS ADMIN BACKEND V1

BACKEND FILE
app/routes/admin.py

Replace the existing file in:
E:\Makwande_Careers_Backend\makwande-Careers-backend\app\routes\admin.py

This backend provides:
- Protected administrator access
- Dashboard KPIs
- User list with search, status and role filters
- User detail endpoint
- Activate and suspend account controls
- Candidate, employer and administrator role controls
- Self-lockout protection for administrators
- Payments search and status filtering
- Activity and audit-log feeds
- Pagination metadata

ENDPOINTS
GET    /api/admin/dashboard
GET    /api/admin/overview
GET    /api/admin/users
GET    /api/admin/users/{user_id}
PATCH  /api/admin/users/{user_id}
GET    /api/admin/payments
GET    /api/admin/transactions
GET    /api/admin/activity
GET    /api/admin/audit-logs

VALIDATE
python -m compileall app

RUN LOCALLY
uvicorn app.main:app --reload

PUSH
git add app/routes/admin.py
git commit -m "feat: complete admin management backend v1"
git push origin main

RENDER
Confirm ADMIN_EMAIL contains the email address used to access the admin portal.
After the push, wait for the Render deployment to complete and hard-refresh the frontend.
