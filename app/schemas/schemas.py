from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from app.models.models import UserRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    surname: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=50)
    middle_name: str = Optional[Field(..., min_length=1, max_length=50)]
    email: EmailStr
    password: str = Field(..., min_length=3, json_schema_extra={"format": "password"})
    password_confirm: str = Field(..., json_schema_extra={"format": "password"})

class UserUpdate(BaseModel):
    surname: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, min_length=1, max_length=50)

class UserOwnUpdate(UserUpdate):
    email: Optional[EmailStr] = None

class UserShow(BaseModel):
    surname: str
    name: str
    middle_name: Optional[str] = None
    email: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)

class UserManagerShow(UserShow):
    id: int
    is_active: bool