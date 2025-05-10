from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr

# レスポンスとして返すユーザー情報
class UserInDBBase(UserBase):
    id: uuid.UUID
    username: str
    email: EmailStr

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }


class UserResponse(UserInDBBase):
    pass