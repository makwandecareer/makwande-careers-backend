# Makwande Careers Recruitment Platform v5

Version 5 extends the existing Version 4.1 backend into a structured recruitment platform.

## Added modules

- Employer registration request
- Employer company profile
- Employer verification status
- Job posting and employer job management
- Candidate job search
- Candidate saved jobs
- Job applications
- Employer application review
- Candidate shortlisting
- Candidate invitations
- Interview scheduling
- Candidate notifications
- Candidate dashboard
- Employer dashboard
- Admin overview
- Audit logs

## Installation

Copy the contents of this ZIP into:

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

The API version should be:

```text
5.0.0
```

## Role note

New users are still registered as candidates by default.

For employer testing, update a test account role in PostgreSQL to:

```text
employer
```

For administration testing, update a separate account role to:

```text
admin
```

Do not convert your primary candidate test account.
