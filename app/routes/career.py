from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas import CareerGuidanceRequest, CareerGuidanceResponse
from app.services.career import generate_career_guidance

router = APIRouter(prefix="/career", tags=["Career Guidance"])

@router.post("/guidance", response_model=CareerGuidanceResponse)
def career_guidance(
    payload: CareerGuidanceRequest,
    _user: dict = Depends(get_current_user),
):
    return generate_career_guidance(payload)
