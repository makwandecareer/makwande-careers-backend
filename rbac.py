from functools import wraps
from fastapi import HTTPException

def require_role(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user=kwargs.get("current_user")
            if user is None or getattr(user,"role",None) not in allowed_roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return func(*args, **kwargs)
        return wrapper
    return decorator
