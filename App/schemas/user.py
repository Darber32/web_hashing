from pydantic import BaseModel, EmailStr


class User_Create(BaseModel):
    email: EmailStr
    password: str


class User_Login(BaseModel):
    email: EmailStr
    password: str