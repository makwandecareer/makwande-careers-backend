from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.database import get_connection, now_iso, row_to_user
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest):
    email = payload.email.lower().strip()

    with get_connection() as db:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        user_id = str(uuid4())
        db.execute(
            '''
            INSERT INTO users (id, email, full_name, password_hash, role, is_active, created_at)
            VALUES (?, ?, ?, ?, 'candidate', 1, ?)
            ''',
            (
                user_id,
                email,
                payload.full_name.strip(),
                hash_password(payload.password),
                now_iso(),
            ),
        )
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    user = row_to_user(row)
    user.pop("password_hash", None)
    return user

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    with get_connection() as db:
        row = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (payload.email.lower().strip(),),
        ).fetchone()

    user = row_to_user(row)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account disabled")

    return TokenResponse(
        access_token=create_access_token(user["id"], user["role"])
    )
