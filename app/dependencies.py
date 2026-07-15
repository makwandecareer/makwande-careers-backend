import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.database import get_connection
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)
def current_user(credentials: HTTPAuthorizationCredentials|None=Depends(bearer)):
    if credentials is None: raise HTTPException(401,'Authentication required')
    try: user_id = decode_token(credentials.credentials)['sub']
    except (jwt.InvalidTokenError, KeyError) as exc: raise HTTPException(401,'Invalid or expired token') from exc
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE id=%s',(user_id,)); user=cur.fetchone()
    if not user or not user['is_active']: raise HTTPException(401,'User unavailable')
    return user

def roles(*allowed):
    def check(user=Depends(current_user)):
        if user['role'] not in allowed: raise HTTPException(403,'Insufficient permissions')
        return user
    return check
