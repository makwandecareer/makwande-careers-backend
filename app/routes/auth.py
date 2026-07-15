from uuid import uuid4
from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.security import hash_password, verify_password, create_token
router=APIRouter(prefix='/auth',tags=['Authentication'])
@router.post('/register',status_code=201)
def register(p:RegisterRequest):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM users WHERE email=%s',(p.email.lower(),))
            if cur.fetchone(): raise HTTPException(409,'Email already registered')
            cur.execute('INSERT INTO users(id,email,full_name,password_hash) VALUES(%s,%s,%s,%s) RETURNING id,email,full_name,role,is_active,created_at',(str(uuid4()),p.email.lower(),p.full_name.strip(),hash_password(p.password))); row=cur.fetchone()
        conn.commit(); return row
@router.post('/login',response_model=TokenResponse)
def login(p:LoginRequest):
    with get_connection() as conn:
        with conn.cursor() as cur: cur.execute('SELECT * FROM users WHERE email=%s',(p.email.lower(),)); user=cur.fetchone()
    if not user or not verify_password(p.password,user['password_hash']): raise HTTPException(401,'Invalid email or password')
    return TokenResponse(access_token=create_token(str(user['id']),user['role']))
