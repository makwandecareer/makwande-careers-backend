from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr; full_name: str = Field(min_length=2,max_length=200); password: str = Field(min_length=12,max_length=128)
class LoginRequest(BaseModel): email: EmailStr; password: str
class TokenResponse(BaseModel): access_token: str; token_type: str = 'bearer'
class ProfileIn(BaseModel):
    phone: str|None=None; location: str|None=None; professional_title: str|None=None; professional_summary: str|None=None; linkedin_url: str|None=None; portfolio_url: str|None=None; visibility: Literal['private','employers']='private'
class EducationIn(BaseModel):
    institution: str; qualification: str; field_of_study: str|None=None; start_date: date|None=None; end_date: date|None=None; description: str|None=None
class ExperienceIn(BaseModel):
    company: str; job_title: str; start_date: date|None=None; end_date: date|None=None; description: str|None=None; achievements: list[str]=[]
class SkillIn(BaseModel): name: str; proficiency: str|None=None
class CVIn(BaseModel):
    title: str; target_role: str|None=None; template_key: str='ats-standard'; content: dict[str,Any]={}; is_public_to_employers: bool=False
class CVUpdate(CVIn): version: int
class CareerGuidanceIn(BaseModel): target_role: str; skills: list[str]=[]; qualifications: list[str]=[]
