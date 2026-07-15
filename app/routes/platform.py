import json
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_connection
from app.dependencies import current_user, roles
from app.schemas import ProfileIn, EducationIn, ExperienceIn, SkillIn, CVIn, CVUpdate, CareerGuidanceIn
router=APIRouter(tags=['Platform'])
@router.get('/users/me')
def me(user=Depends(current_user)): return {k:v for k,v in user.items() if k!='password_hash'}
@router.put('/profile')
def profile(p:ProfileIn,user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''INSERT INTO profiles(id,user_id,phone,location,professional_title,professional_summary,linkedin_url,portfolio_url,visibility) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(user_id) DO UPDATE SET phone=EXCLUDED.phone,location=EXCLUDED.location,professional_title=EXCLUDED.professional_title,professional_summary=EXCLUDED.professional_summary,linkedin_url=EXCLUDED.linkedin_url,portfolio_url=EXCLUDED.portfolio_url,visibility=EXCLUDED.visibility,updated_at=NOW() RETURNING *''',(str(uuid4()),user['id'],p.phone,p.location,p.professional_title,p.professional_summary,p.linkedin_url,p.portfolio_url,p.visibility)); row=cur.fetchone()
        conn.commit(); return row
@router.post('/education',status_code=201)
def add_education(p:EducationIn,user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO education(id,user_id,institution,qualification,field_of_study,start_date,end_date,description) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',(str(uuid4()),user['id'],p.institution,p.qualification,p.field_of_study,p.start_date,p.end_date,p.description)); row=cur.fetchone()
        conn.commit(); return row
@router.get('/education')
def education(user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur: cur.execute('SELECT * FROM education WHERE user_id=%s',(user['id'],)); return cur.fetchall()
@router.post('/experience',status_code=201)
def add_experience(p:ExperienceIn,user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO experience(id,user_id,company,job_title,start_date,end_date,description,achievements) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING *',(str(uuid4()),user['id'],p.company,p.job_title,p.start_date,p.end_date,p.description,json.dumps(p.achievements))); row=cur.fetchone()
        conn.commit(); return row
@router.get('/experience')
def experience(user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur: cur.execute('SELECT * FROM experience WHERE user_id=%s',(user['id'],)); return cur.fetchall()
@router.post('/skills',status_code=201)
def add_skill(p:SkillIn,user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            try: cur.execute('INSERT INTO skills(id,user_id,name,proficiency) VALUES(%s,%s,%s,%s) RETURNING *',(str(uuid4()),user['id'],p.name,p.proficiency)); row=cur.fetchone()
            except Exception as exc: raise HTTPException(409,'Skill already exists') from exc
        conn.commit(); return row
@router.get('/skills')
def skills(user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur: cur.execute('SELECT * FROM skills WHERE user_id=%s ORDER BY name',(user['id'],)); return cur.fetchall()
@router.post('/cvs',status_code=201)
def create_cv(p:CVIn,user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO cvs(id,owner_id,title,target_role,template_key,content,is_public_to_employers) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING *',(str(uuid4()),user['id'],p.title,p.target_role,p.template_key,json.dumps(p.content),p.is_public_to_employers)); row=cur.fetchone()
        conn.commit(); return row
@router.get('/cvs')
def cvs(user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur: cur.execute('SELECT * FROM cvs WHERE owner_id=%s ORDER BY updated_at DESC',(user['id'],)); return cur.fetchall()
@router.put('/cvs/{cv_id}')
def update_cv(cv_id:str,p:CVUpdate,user=Depends(current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE cvs SET title=%s,target_role=%s,template_key=%s,content=%s::jsonb,is_public_to_employers=%s,version=version+1,updated_at=NOW() WHERE id=%s AND owner_id=%s AND version=%s RETURNING *',(p.title,p.target_role,p.template_key,json.dumps(p.content),p.is_public_to_employers,cv_id,user['id'],p.version)); row=cur.fetchone()
            if not row: raise HTTPException(409,'CV not found or version conflict')
        conn.commit(); return row
@router.get('/employers/candidates')
def candidates(user=Depends(roles('employer','admin'))):
    with get_connection() as conn:
        with conn.cursor() as cur: cur.execute("SELECT c.* FROM cvs c JOIN profiles p ON p.user_id=c.owner_id WHERE c.is_public_to_employers=TRUE AND p.visibility='employers' ORDER BY c.updated_at DESC LIMIT 100"); return cur.fetchall()
@router.post('/career/guidance')
def guidance(p:CareerGuidanceIn,user=Depends(current_user)):
    return {'strengths':p.skills[:5] or ['Profile requires assessment'],'gaps':[f'Compare your evidence with current {p.target_role} requirements.'],'next_steps':['Review three current job descriptions.','Identify recurring requirements.','Match each requirement to verified evidence.','Build a practical project for the main gap.']}
