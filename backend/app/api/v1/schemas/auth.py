from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str
    name: str
    company_name: str


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserResponse(BaseModel):
    """User data response"""
    id: UUID
    email: str
    name: str
    company_id: UUID
    role: str
    is_active: bool
    onboarding_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyResponse(BaseModel):
    """Company data response"""
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
