import uuid
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import app_logger
from app.core.redis import get_password_from_redis, delete_password_from_redis
from app.db.session import get_async_session
from app.crud.auth_user import auth_user_crud
from app.schemas.auth_user import AuthUserCreateDB


async def handle_user_creation_response(user_data: Dict[str, Any]):
    """
    user-serviceから受け取ったユーザー作成レスポンスを処理する
    
    Args:
        user_data: ユーザーデータ（id, username, email, original_requestなど）
    """
    logger = app_logger
    logger.info(f"ユーザー作成レスポンスの処理を開始: {user_data}")

    # ステータスの確認
    status = user_data.get("status")
    if status == "error":
        # エラーの場合の処理
        error_type = user_data.get("error_type")
        error_message = user_data.get("message")
        original_request = user_data.get("original_request", {})
        password_key = original_request.get("password_key")

        logger.error(f"ユーザー作成エラー: {error_type} - {error_message}")

        # Redisからパスワードを削除（クリーンアップ）
        if password_key:
            delete_result = await delete_password_from_redis(password_key)
            if delete_result:
                logger.info(f"一時保存されたパスワードを削除しました: key={password_key}")
            else:
                logger.warning(f"一時保存されたパスワードの削除に失敗しました: key={password_key}")
        
        # エラー情報をRedisに保存（フロントエンドからのポーリング用）
        # 実装例: await save_registration_error_to_redis(original_request.get("username"), error_message)
        return
    
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
        password_key = original_request.get("password_key")
        
        if not username or not email or not password_key:
            logger.error(f"必要なユーザー情報が不足しています: username={username}, email={email}, password_key={password_key}")
            return
        
        # Redisからパスワードを取得
        password = await get_password_from_redis(password_key)
        if not password:
            logger.error(f"パスワードの取得に失敗しました: key={password_key}")
            return
        
        # AsyncSessionの取得
        async for session in get_async_session():
            try:
                # ユーザー作成スキーマの作成
                user_create = AuthUserCreateDB(
                    username=username,
                    email=email,
                    password=password,
                    user_id=uuid.UUID(user_id)
                )
                
                # ユーザーの作成（user_idを指定）
                new_user = await auth_user_crud.create(
                    session, 
                    user_create
                )
                
                logger.info(f"auth-serviceでユーザーを作成しました: ID={new_user.id}, user_id={new_user.user_id}")
                
                # 処理完了後、Redisからパスワード情報を削除（クリーンアップ）
                delete_result = await delete_password_from_redis(password_key)
                if delete_result:
                    logger.info(f"一時保存されたパスワードを削除しました: key={password_key}")
                else:
                    logger.warning(f"一時保存されたパスワードの削除に失敗しました: key={password_key}")
                
            except Exception as e:
                logger.error(f"ユーザー作成処理中にエラーが発生しました: {str(e)}", exc_info=True)
                # セッションのロールバック
                await session.rollback()
                raise
    except Exception as e:
        logger.error(f"ユーザー作成レスポンス処理中にエラーが発生しました: {str(e)}", exc_info=True)
