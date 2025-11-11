from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(..., min_length=8, pattern=r"[a-zA-Z0-9]+")

    class Config:
        from_attributes = True


class VerifyCodeSchema(BaseModel):
    code: str
