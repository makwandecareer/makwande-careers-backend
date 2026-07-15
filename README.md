# Makwande Careers Simple Backend

A lightweight backend for the Makwande Careers platform.

## What this version includes

- User registration and login
- Secure password hashing
- JWT authentication
- Candidate, CV builder, employer and admin roles
- CV creation, editing, listing and deletion
- Employer access to public candidate CVs
- Career guidance endpoint
- AI-ready service layer
- SQLite database
- No Docker
- No SQLAlchemy
- Simple project structure

## Technology

- Python 3.12+
- FastAPI
- SQLite through Python's built-in `sqlite3`
- Pydantic
- PyJWT
- pwdlib with Argon2

## Setup

### 1. Open the project folder

```bash
cd makwande-simple-backend
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install packages

```bash
pip install -r requirements.txt
```

### 4. Create the environment file

Copy `.env.example` to `.env`.

Generate a secure JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Paste it into `.env`.

### 5. Start the backend

```bash
uvicorn app.main:app --reload
```

### 6. Open API documentation

```text
http://127.0.0.1:8000/docs
```

## Main API routes

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/me`
- `POST /api/cvs`
- `GET /api/cvs`
- `GET /api/cvs/{cv_id}`
- `PUT /api/cvs/{cv_id}`
- `DELETE /api/cvs/{cv_id}`
- `GET /api/employers/candidates`
- `POST /api/career/guidance`

## Global-standard foundations included

- Strong password hashing
- Short-lived access tokens
- Role-based access control
- Input validation
- Ownership checks
- Structured error responses
- Security headers
- Environment-based configuration
- Privacy control for candidate visibility
- Clean separation between routes, database and services

## Before public launch

Add:

- Email verification
- Password reset
- Rate limiting
- HTTPS
- Database backups
- Audit logging
- POPIA/GDPR privacy policy
- Payment processing
- Monitoring and error reporting
- Penetration testing
