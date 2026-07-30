from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(password:str, hashed:str)->bool:
    return pwd_context.verify(password, hashed)

def create_access_token(subject:str, secret:str, algorithm:str="HS256", minutes:int=60)->str:
    payload={
        "sub": subject,
        "exp": datetime.now(timezone.utc)+timedelta(minutes=minutes)
    }
    return jwt.encode(payload, secret, algorithm=algorithm)
