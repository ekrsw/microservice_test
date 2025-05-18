from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class AuthUserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator("username", mode="after")
    def username_alphanumeric(cls, v):
        if v is None:  # Noneの場合はスキップ
            return v
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("ユーザーネームは半角英数字とアンダースコア(_)のみ使用可能です")
        return v


class AuthUserCreate(AuthUserBase):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=16)
    # user_idはregisterエンドポイントでは不要 (user-serviceから提供される)

    @field_validator("password", mode="after")
    def password_alphanumeric(cls, v):
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("パスワードは半角英数字のみ使用可能です")
        return v


# CRUD処理用のスキーマ（user_idが必須）
class AuthUserCreateDB(AuthUserCreate):
    user_id: uuid.UUID = Field(...)


class AuthUserUpdate(AuthUserBase):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    user_id: Optional[uuid.UUID] = None
    # passwordは更新しない


class AuthUserUpdatePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=1, max_length=16)

    @field_validator("new_password", mode="after")
    def password_alphanumeric(cls, v):
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("パスワードは半角英数字のみ使用可能です")
        return v


# レスポンスとして返すユーザー情報
class AuthUserInDBBase(AuthUserBase):
    id: uuid.UUID
    username: str
    email: EmailStr
    user_id: Optional[uuid.UUID] = None

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }


class AuthUserResponse(AuthUserInDBBase):
    pass


# トークン関連のスキーマ
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None


# リフレッシュトークンリクエスト用のスキーマ（access_tokenを必須とする）
class RefreshTokenRequest(BaseModel):
    refresh_token: str
    access_token: str


# ログアウトリクエスト用のスキーマ（access_tokenを必須とする）
class LogoutRequest(BaseModel):
    refresh_token: str
    access_token: str
