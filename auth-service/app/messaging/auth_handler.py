import uuid
import json
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from aio_pika import IncomingMessage

from app.core.logging import app_logger
from app.core.redis import get_password_from_redis, delete_password_from_redis
from app.db.session import get_async_session
from app.crud.auth_user import auth_user_crud
from app.schemas.auth_user import AuthUserCreateDB


async def handle_user_creation_response(message: IncomingMessage):
    """
    user-serviceから受け取ったユーザー作成レスポンスを処理する
    
    Args:
        message: RabbitMQから受け取ったメッセージ
    """
    logger = app_logger
    logger.info(f"ユーザー作成レスポンスの処理を開始: {message}")
    
    try:
        # メッセージボディからJSONデータを取得
        message_body = message.body.decode('utf-8')
        user_data = json.loads(message_body)
    except json.JSONDecodeError:
        logger.error("ユーザー作成レスポンスのJSONデコードに失敗しました")
        await message.ack()  # エラー時も確認済みとしてメッセージを処理
        return
    except Exception as e:
        logger.error(f"メッセージ処理中に予期しないエラーが発生しました: {str(e)}")
        await message.ack()
        return

    # 必須フィールドの確認
    if "user_id" not in user_data:
        logger.error("ユーザーIDが含まれていません")
        await message.ack()
        return
    
    # ステータスの確認
    status = user_data.get("status")
    if status == "failure":
        # 失敗の場合の処理
        user_id = user_data.get("user_id")
        error_message = user_data.get("message", "不明なエラー")
        
        logger.warning(f"ユーザー作成に失敗しました: {error_message}, user_id={user_id}")
        
        # user_idに基づいてユーザーを削除
        try:
            async for session in get_async_session():
                await auth_user_crud.delete_by_user_id(session, user_id)
                await session.commit()
        except Exception as e:
            logger.error(f"ユーザー削除中にエラーが発生しました: {str(e)}")
        
        await message.ack()
        return
    
    # 成功の場合の処理
    if status == "success":
        user_id = user_data.get("user_id")
        
        # ユーザーを有効化
        try:
            async for session in get_async_session():
                # ユーザーの有効化
                activated_user = await auth_user_crud.activate_user(session, user_id)
                await session.commit()
                
                logger.info(f"ユーザーを有効化しました: user_id={user_id}")
        except Exception as e:
            logger.error(f"ユーザー有効化処理中にエラーが発生しました: {str(e)}", exc_info=True)
    
    # 常にメッセージを確認済みとしてマーク
    await message.ack()
