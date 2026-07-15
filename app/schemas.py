from typing import Any, Literal
from pydantic import BaseModel, EmailStr, Field

UserRole = Literal["candidate", "cv_builder", "employer", "admin"]

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=12, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: str

class CVCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    target_role: str | None = Field(default=None, max_length=160)
    content: dict[str, Any] = Field(default_factory=dict)
    is_public_to_employers: bool = False

class CVUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    target_role: str | None = Field(default=None, max_length=160)
    content: dict[str, Any]
    is_public_to_employers: bool
    version: int = Field(ge=1)

class CVResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    target_role: str | None
    content: dict[str, Any]
    is_public_to_employers: bool
    version: int
    created_at: str
    updated_at: str

class CareerGuidanceRequest(BaseModel):
    current_role: str | None = Field(default=None, max_length=160)
    target_role: str = Field(min_length=2, max_length=160)
    skills: list[str] = Field(default_factory=list, max_length=100)
    qualifications: list[str] = Field(default_factory=list, max_length=50)

class CareerGuidanceResponse(BaseModel):
    strengths: list[str]
    gaps: list[str]
    next_steps: list[str]
