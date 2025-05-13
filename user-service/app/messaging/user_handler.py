import uuid
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import app_logger
from app.db.session import get_async_session
from app.crud.exceptions import (
    DuplicateEmailError,
    DuplicateUsernameError
)
from app.crud.user import user_crud
from app.schemas.user import UserCreate
from app.messaging.rabbitmq import publish_user_created


# user-service/app/messaging/user_handler.py の修正
async def handle_user_creation_request(user_data: Dict[str, Any]):
    logger = app_logger
    logger.info(f"ユーザー作成リクエストの処理を開始: {user_data}")
    
    try:
        async for session in get_async_session():
            try:
                # ユーザー作成スキーマの作成
                user_create = UserCreate(
                    username=user_data.get("username"),
                    email=user_data.get("email")
                )
                
                # ユーザーの作成
                new_user = await user_crud.create(session, user_create)
                logger.info(f"ユーザーを作成しました: ID={new_user.id}, username={new_user.username}")
                
                # auth-serviceに返信するデータの準備
                response_data = {
                    "id": new_user.id,
                    "username": new_user.username,
                    "email": new_user.email,
                    "status": "success",
                    "original_request": user_data  # 元のリクエストデータも含める
                }
                
                # auth-serviceにユーザー作成完了メッセージを送信
                await publish_user_created(response_data)
                logger.info(f"auth-serviceにユーザー作成完了メッセージを送信しました: user_id={new_user.id}")
                
            except DuplicateEmailError:
                logger.error(f"ユーザー作成失敗: メールアドレスが重複しています: {user_data.get('email')}")
                # エラーレスポンスの送信
                error_response = {
                    "status": "error",
                    "error_type": "duplicate_email",
                    "message": "メールアドレスが既に使用されています",
                    "original_request": user_data
                }
                await publish_user_created(error_response)
                
            except DuplicateUsernameError:
                logger.error(f"ユーザー作成失敗: ユーザー名が重複しています: {user_data.get('username')}")
                # エラーレスポンスの送信
                error_response = {
                    "status": "error",
                    "error_type": "duplicate_username",
                    "message": "ユーザー名が既に使用されています",
                    "original_request": user_data
                }
                await publish_user_created(error_response)
                
            except Exception as e:
                logger.error(f"ユーザー作成処理中にエラーが発生しました: {str(e)}", exc_info=True)
                # セッションのロールバック
                await session.rollback()
                # 一般的なエラーレスポンスの送信
                error_response = {
                    "status": "error",
                    "error_type": "internal_error",
                    "message": f"ユーザー作成中にエラーが発生しました: {str(e)}",
                    "original_request": user_data
                }
                await publish_user_created(error_response)
                
    except Exception as e:
        logger.error(f"セッション取得中にエラーが発生しました: {str(e)}", exc_info=True)
        # セッション取得エラーのレスポンス送信
        error_response = {
            "status": "error",
            "error_type": "session_error",
            "message": "データベース接続エラー",
            "original_request": user_data
        }
        await publish_user_created(error_response)

