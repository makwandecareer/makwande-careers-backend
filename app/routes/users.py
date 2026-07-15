from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    user = dict(user)
    user.pop("password_hash", None)
    return user
