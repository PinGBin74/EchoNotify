from pydantic import BaseModel, EmailStr


class UserLoginRequestSchema(BaseModel):
    email: EmailStr
    password: str


class UserLoginSchema(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str


class UserLoginResponseSchema(BaseModel):
    user_id: int
    access_token: str


class Config:
    from_attributes = True
