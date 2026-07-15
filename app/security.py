from datetime import UTC, datetime, timedelta
from uuid import uuid4
import jwt
from pwdlib import PasswordHash
from app.config import settings

_hasher = PasswordHash.recommended()
def hash_password(password: str) -> str: return _hasher.hash(password)
def verify_password(password: str, hashed: str) -> bool: return _hasher.verify(password, hashed)
def create_token(user_id: str, role: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode({'sub': user_id, 'role': role, 'type':'access', 'iat': now, 'exp': now + timedelta(minutes=settings.access_token_minutes), 'jti': str(uuid4())}, settings.jwt_secret, algorithm='HS256')
def decode_token(token: str) -> dict:
    data = jwt.decode(token, settings.jwt_secret, algorithms=['HS256'])
    if data.get('type') != 'access': raise jwt.InvalidTokenError('invalid token type')
    return data
