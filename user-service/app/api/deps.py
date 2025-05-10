from uuid import UUID

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_async_session
from app.crud.user import user_crud
from app.models.user import User

from app.core.config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.AUTH_SERVICE_URL)

async def validate_token(token: str) -> dict:
    """
    トークンを検証し、ペイロードを返す
    """
    try:
        # JWTの署名検証
        payload = jwt.decode(
            token, 
            settings.PUBLIC_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False}
        )
        
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンです",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    現在のユーザーを取得する
    """
    try:
        # トークンの検証
        payload = await validate_token(token)
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンです",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"認証に失敗しました: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ユーザーの取得
    db_user = await user_crud.get_by_id(db, UUID(user_id))
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    
    return db_user