from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class AuthRequest(BaseModel):
    email: str
    password: str

class JobApplication(BaseModel):
    job_name: str
    company_name: str
    status: str
    link: Optional[str] = ""
    salary: Optional[str] = ""
    uid: UUID
    id: UUID

class JobApplicationCreate(BaseModel):
    job_name: str
    company_name: str
    status: str
    link: Optional[str] = ""
    salary: Optional[str] = ""
    uid: UUID

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str
    occupation: str
    location: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str