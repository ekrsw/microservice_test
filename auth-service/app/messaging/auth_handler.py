import uuid
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import app_logger
from app.db.session import get_async_session
from app.crud.auth_user import auth_user_crud
from app.schemas.auth_user import AuthUserCreate


async def handle_user_creation_response(user_data: Dict[str, Any]):
    """
    user-serviceから受け取ったユーザー作成レスポンスを処理する
    
    Args:
        user_data: ユーザーデータ（id, username, email, original_requestなど）
    """
    logger = app_logger
    logger.info(f"ユーザー作成レスポンスの処理を開始: {user_data}")
    
    try:
        # user_idの取得
        user_id = user_data.get("id")
        if not user_id:
            logger.error("ユーザーIDが含まれていません")
            return
        
        # 元のリクエストデータの取得
        original_request = user_data.get("original_request", {})
        username = original_request.get("username")
        email = original_request.get("email")
        password = original_request.get("password")  # 本来はRedisなどから取得する必要がある
        
        if not username or not email or not password:
            logger.error(f"必要なユーザー情報が不足しています: username={username}, email={email}")
            return
        
        # AsyncSessionの取得
        async for session in get_async_session():
            try:
                # ユーザー作成スキーマの作成
                user_create = AuthUserCreate(
                    username=username,
                    email=email,
                    password=password
                )
                
                # ユーザーの作成（user_idを指定）
                new_user = await auth_user_crud.create_with_user_id(
                    session, 
                    user_create, 
                    uuid.UUID(user_id)
                )
                
                logger.info(f"auth-serviceでユーザーを作成しました: ID={new_user.id}, user_id={new_user.user_id}")
                
            except Exception as e:
                logger.error(f"ユーザー作成処理中にエラーが発生しました: {str(e)}", exc_info=True)
                # セッションのロールバック
                await session.rollback()
                raise
    except Exception as e:
        logger.error(f"ユーザー作成レスポンス処理中にエラーが発生しました: {str(e)}", exc_info=True)
