import json
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_connection
from app.dependencies import get_current_user, require_roles
from app.schemas_v4 import CertificationIn, ProjectIn, LanguageIn, ReferenceIn, EmployerProfileIn, JobIn, ApplicationIn, ApplicationStatusUpdate, ShortlistIn

router = APIRouter()

def employer_for_user(user_id: str):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('SELECT * FROM employers WHERE owner_user_id=%s', (user_id,))
            row = cur.fetchone()
    if row is None:
        raise HTTPException(404, 'Employer profile not found')
    return row

@router.post('/certifications', status_code=201, tags=['Certifications'])
def add_certification(p: CertificationIn, user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('''INSERT INTO certifications (id,user_id,name,issuer,issue_date,expiry_date,credential_id,credential_url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''', (str(uuid4()),user['id'],p.name,p.issuer,p.issue_date,p.expiry_date,p.credential_id,p.credential_url))
            row=cur.fetchone()
        c.commit()
    return row

@router.get('/certifications', tags=['Certifications'])
def certifications(user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('SELECT * FROM certifications WHERE user_id=%s ORDER BY issue_date DESC NULLS LAST',(user['id'],))
            return cur.fetchall()

@router.post('/projects', status_code=201, tags=['Projects'])
def add_project(p: ProjectIn, user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('''INSERT INTO projects (id,user_id,name,description,project_url,technologies,start_date,end_date) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s) RETURNING *''',(str(uuid4()),user['id'],p.name,p.description,p.project_url,json.dumps(p.technologies),p.start_date,p.end_date))
            row=cur.fetchone()
        c.commit()
    return row

@router.get('/projects', tags=['Projects'])
def projects(user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('SELECT * FROM projects WHERE user_id=%s ORDER BY start_date DESC NULLS LAST',(user['id'],))
            return cur.fetchall()

@router.post('/languages', status_code=201, tags=['Languages'])
def add_language(p: LanguageIn, user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            try:
                cur.execute('INSERT INTO languages (id,user_id,name,proficiency) VALUES (%s,%s,%s,%s) RETURNING *',(str(uuid4()),user['id'],p.name,p.proficiency))
                row=cur.fetchone()
            except Exception as exc:
                raise HTTPException(409,'Language already exists') from exc
        c.commit()
    return row

@router.get('/languages', tags=['Languages'])
def languages(user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('SELECT * FROM languages WHERE user_id=%s ORDER BY name',(user['id'],))
            return cur.fetchall()

@router.post('/references', status_code=201, tags=['References'])
def add_reference(p: ReferenceIn, user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('''INSERT INTO candidate_references (id,user_id,full_name,relationship,company,email,phone) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *''',(str(uuid4()),user['id'],p.full_name,p.relationship,p.company,str(p.email) if p.email else None,p.phone))
            row=cur.fetchone()
        c.commit()
    return row

@router.get('/references', tags=['References'])
def references(user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('SELECT * FROM candidate_references WHERE user_id=%s ORDER BY full_name',(user['id'],))
            return cur.fetchall()

@router.get('/templates', tags=['CV Templates'])
def templates():
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('SELECT * FROM cv_templates WHERE is_active=TRUE ORDER BY name')
            return cur.fetchall()

@router.put('/employer/profile', tags=['Employer Portal'])
def employer_profile(p: EmployerProfileIn, user=Depends(require_roles('employer','admin'))):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('''INSERT INTO employers (id,owner_user_id,company_name,website_url,industry,location,description) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (owner_user_id) DO UPDATE SET company_name=EXCLUDED.company_name,website_url=EXCLUDED.website_url,industry=EXCLUDED.industry,location=EXCLUDED.location,description=EXCLUDED.description,updated_at=NOW() RETURNING *''',(str(uuid4()),user['id'],p.company_name,p.website_url,p.industry,p.location,p.description))
            row=cur.fetchone()
        c.commit()
    return row

@router.post('/jobs', status_code=201, tags=['Jobs'])
def create_job(p: JobIn, user=Depends(require_roles('employer','admin'))):
    e=employer_for_user(user['id'])
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('''INSERT INTO jobs (id,employer_id,title,location,employment_type,workplace_type,description,requirements,skills,closing_date,is_active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s) RETURNING *''',(str(uuid4()),e['id'],p.title,p.location,p.employment_type,p.workplace_type,p.description,json.dumps(p.requirements),json.dumps(p.skills),p.closing_date,p.is_active))
            row=cur.fetchone()
        c.commit()
    return row

@router.get('/jobs', tags=['Jobs'])
def jobs(search: str|None=Query(default=None,max_length=120), location: str|None=Query(default=None,max_length=120), limit:int=Query(default=50,ge=1,le=100)):
    conditions=['j.is_active=TRUE']; params=[]
    if search:
        conditions.append('(j.title ILIKE %s OR j.description ILIKE %s)'); params += [f'%{search}%',f'%{search}%']
    if location:
        conditions.append('j.location ILIKE %s'); params.append(f'%{location}%')
    params.append(limit)
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute(f'''SELECT j.*,e.company_name,e.industry FROM jobs j JOIN employers e ON e.id=j.employer_id WHERE {' AND '.join(conditions)} ORDER BY j.created_at DESC LIMIT %s''',tuple(params))
            return cur.fetchall()

@router.post('/applications', status_code=201, tags=['Applications'])
def apply(p: ApplicationIn, user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('SELECT id FROM cvs WHERE id=%s AND owner_id=%s',(p.cv_id,user['id']))
            if cur.fetchone() is None: raise HTTPException(404,'CV not found')
            try:
                cur.execute('''INSERT INTO applications (id,job_id,candidate_user_id,cv_id,cover_note) VALUES (%s,%s,%s,%s,%s) RETURNING *''',(str(uuid4()),p.job_id,user['id'],p.cv_id,p.cover_note))
                row=cur.fetchone()
            except Exception as exc:
                raise HTTPException(409,'Application already exists or job is unavailable') from exc
        c.commit()
    return row

@router.get('/applications/me', tags=['Applications'])
def my_applications(user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('''SELECT a.*,j.title AS job_title,e.company_name FROM applications a JOIN jobs j ON j.id=a.job_id JOIN employers e ON e.id=j.employer_id WHERE a.candidate_user_id=%s ORDER BY a.created_at DESC''',(user['id'],))
            return cur.fetchall()

@router.get('/employer/applications', tags=['Employer Portal'])
def employer_applications(user=Depends(require_roles('employer','admin'))):
    e=employer_for_user(user['id'])
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('''SELECT a.*,j.title AS job_title,u.full_name,u.email FROM applications a JOIN jobs j ON j.id=a.job_id JOIN users u ON u.id=a.candidate_user_id WHERE j.employer_id=%s ORDER BY a.created_at DESC''',(e['id'],))
            return cur.fetchall()

@router.put('/applications/{application_id}/status', tags=['Employer Portal'])
def set_status(application_id:str,p:ApplicationStatusUpdate,user=Depends(require_roles('employer','admin'))):
    e=employer_for_user(user['id'])
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('''UPDATE applications a SET status=%s,updated_at=NOW() FROM jobs j WHERE a.id=%s AND a.job_id=j.id AND j.employer_id=%s RETURNING a.*''',(p.status,application_id,e['id']))
            row=cur.fetchone()
        c.commit()
    if row is None: raise HTTPException(404,'Application not found')
    return row

@router.post('/employer/shortlists', status_code=201, tags=['Employer Portal'])
def shortlist(p:ShortlistIn,user=Depends(require_roles('employer','admin'))):
    e=employer_for_user(user['id'])
    with get_connection() as c:
        with c.cursor() as cur:
            try:
                cur.execute('INSERT INTO shortlists (id,employer_id,candidate_user_id,job_id,notes) VALUES (%s,%s,%s,%s,%s) RETURNING *',(str(uuid4()),e['id'],p.candidate_user_id,p.job_id,p.notes))
                row=cur.fetchone()
            except Exception as exc:
                raise HTTPException(409,'Candidate already shortlisted') from exc
        c.commit()
    return row

@router.get('/dashboard/candidate', tags=['Dashboard'])
def candidate_dashboard(user=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute('SELECT COUNT(*) total FROM cvs WHERE owner_id=%s',(user['id'],)); cvs=cur.fetchone()['total']
            cur.execute('SELECT COUNT(*) total FROM applications WHERE candidate_user_id=%s',(user['id'],)); apps=cur.fetchone()['total']
            cur.execute('SELECT COUNT(*) total FROM skills WHERE user_id=%s',(user['id'],)); skills=cur.fetchone()['total']
    return {'cv_count':cvs,'application_count':apps,'skill_count':skills}
