from uuid import uuid4
from datetime import UTC, datetime
from fastapi import APIRouter, HTTPException, Request
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
def login(p:LoginRequest, request: Request):
    with get_connection() as conn:
        with conn.cursor() as cur: cur.execute('SELECT * FROM users WHERE email=%s',(p.email.lower(),)); user=cur.fetchone()
    if not user or not verify_password(p.password,user['password_hash']): raise HTTPException(401,'Invalid email or password')
    if not user['is_active']: raise HTTPException(403,'User account is disabled')
    token = create_token(str(user['id']),user['role'])
    from app.security import decode_token
    payload = decode_token(token)
    forwarded = request.headers.get('x-forwarded-for')
    ip_address = (forwarded.split(',',1)[0].strip() if forwarded else (request.client.host if request.client else None))
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''INSERT INTO user_sessions(id,user_id,token_jti,user_agent,ip_address,expires_at)
                   VALUES(%s,%s,%s,%s,%s,%s)''',
                (str(uuid4()), user['id'], payload['jti'], request.headers.get('user-agent','')[:1000], ip_address, datetime.fromtimestamp(payload['exp'], UTC)),
            )
            cur.execute(
                '''INSERT INTO security_events(id,user_id,event_type,ip_address,user_agent)
                   VALUES(%s,%s,'login',%s,%s)''',
                (str(uuid4()), user['id'], ip_address, request.headers.get('user-agent','')[:1000]),
            )
        conn.commit()
    return TokenResponse(access_token=token)
