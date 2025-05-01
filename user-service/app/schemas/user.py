from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    is_active: Optional[bool] = True
    is_supervisor: Optional[bool] = False
    ctstage_name: Optional[str] = None
    sweet_name: Optional[str] = None