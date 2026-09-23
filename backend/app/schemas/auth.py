from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    iat: Optional[int] = None
    exp: Optional[int] = None


class UserBase(BaseModel):
    username: str
    role: str = "analyst"
    active: int = 1


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserOut(UserBase):
    id: str
    created_at: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str
