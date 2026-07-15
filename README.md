# Makwande Careers PostgreSQL Backend v2

No Docker. No SQLAlchemy. Uses FastAPI, Psycopg and Render PostgreSQL.

## Replace your current files

Copy the contents of this package into your repository root, keeping your `.env` private.

## Render environment

- APP_NAME=Makwande Careers API
- ENVIRONMENT=production
- JWT_SECRET=<long random secret>
- ACCESS_TOKEN_MINUTES=30
- DATABASE_URL=<Render Internal Database URL>
- CORS_ORIGINS=*

## Render commands

Build: `pip install -r requirements.txt`

Start: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Push

`git add .`

`git commit -m "Upgrade backend to PostgreSQL platform v2"`

`git push origin main`
