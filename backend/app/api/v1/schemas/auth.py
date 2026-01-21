from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


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
    id: str
    email: str
    name: str
    company_id: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyResponse(BaseModel):
    """Company data response"""
    id: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
