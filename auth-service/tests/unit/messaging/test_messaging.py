import pytest
from unittest.mock import patch, AsyncMock, MagicMock, call
import json
import uuid

from app.messaging.rabbitmq import rabbitmq_client
from app.messaging.auth_handler import handle_user_creation_response
from app.core.logging import app_logger


# RabbitMQクライアント初期化のテスト
@pytest.mark.asyncio
async def test_rabbitmq_client_initialize():
    """
    RabbitMQクライアントの初期化プロセスをテスト
    """
    # 必要なモックを設定
    with patch("aio_pika.connect_robust", new_callable=AsyncMock) as mock_connect, \
         patch.object(rabbitmq_client, "_connection", None), \
         patch.object(rabbitmq_client, "_channel", None):
        
        # モックの設定
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        # 初期化を実行
        await rabbitmq_client.initialize()
        
        # モックが呼び出されたことを確認
        mock_connect.assert_called_once()
        mock_connection.channel.assert_called_once()
        
        # 接続とチャネルが保存されたことを確認
        assert rabbitmq_client._connection == mock_connection
        assert rabbitmq_client._channel == mock_channel


# RabbitMQクライアントのクローズ処理のテスト
@pytest.mark.asyncio
async def test_rabbitmq_client_close():
    """
    RabbitMQクライアントのクローズ処理をテスト
    """
    # 必要なモックを設定
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    
    with patch.object(rabbitmq_client, "_connection", mock_connection), \
         patch.object(rabbitmq_client, "_channel", mock_channel):
        
        # クローズ処理を実行
        await rabbitmq_client.close()
        
        # 接続のクローズが呼び出されたことを確認
        mock_connection.close.assert_called_once()
        
        # 接続とチャネルがリセットされたことを確認
        assert rabbitmq_client._connection is None
        assert rabbitmq_client._channel is None


# RabbitMQクライアントの接続がない場合のクローズ処理のテスト
@pytest.mark.asyncio
async def test_rabbitmq_client_close_no_connection():
    """
    接続がない場合のRabbitMQクライアントのクローズ処理をテスト
    """
    with patch.object(rabbitmq_client, "_connection", None), \
         patch.object(rabbitmq_client, "_channel", None):
        
        # 例外が発生しないことを確認
        await rabbitmq_client.close()


# ユーザー作成メッセージの公開のテスト
@pytest.mark.asyncio
async def test_publish_user_creation():
    """
    ユーザー作成メッセージの公開をテスト
    """
    # 必要なモックを設定
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()
    mock_channel.default_exchange = mock_exchange
    
    with patch.object(rabbitmq_client, "_channel", mock_channel), \
         patch("aio_pika.Message") as mock_message_class:
        
        # テスト用のデータ
        user_data = {
            "user_id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com"
        }
        
        # モックの設定
        mock_message = MagicMock()
        mock_message_class.return_value = mock_message
        
        # publish メソッドの設定
        mock_exchange.publish.return_value = None
        
        # メッセージ公開を実行
        result = await rabbitmq_client.publish_user_creation(user_data)
        
        # 公開が成功したことを確認
        assert result is True
        
        # メッセージが正しく作成されたことを確認
        mock_message_class.assert_called_once()
        args, kwargs = mock_message_class.call_args
        body = kwargs.get("body", args[0] if args else None)
        assert body is not None
        
        # メッセージがJSONとしてエンコードされていることを確認
        try:
            decoded_body = json.loads(body)
            assert decoded_body == user_data
        except json.JSONDecodeError:
            pytest.fail("Message body is not valid JSON")
        
        # publish が呼び出されたことを確認
        # ここではモックの構造を調整（exchange.publishが直接呼び出される）
        mock_exchange.publish.assert_called_once()


# ユーザー作成レスポンスのコンシューマーセットアップのテスト
@pytest.mark.asyncio
async def test_setup_user_creation_response_consumer():
    """
    ユーザー作成レスポンスのコンシューマーセットアップをテスト
    """
    # 必要なモックを設定
    mock_channel = AsyncMock()
    mock_queue = AsyncMock()
    mock_callback = AsyncMock()
    
    with patch.object(rabbitmq_client, "_channel", mock_channel):
        # キューの宣言をモック
        mock_channel.declare_queue.return_value = mock_queue
        
        # コンシューマーセットアップを実行
        await rabbitmq_client.setup_user_creation_response_consumer(mock_callback)
        
        # キューが宣言されたことを確認
        mock_channel.declare_queue.assert_called_once_with(
            "user_creation_response",
            durable=True
        )
        
        # コンシューマーが設定されたことを確認
        mock_queue.consume.assert_called_once()
        # consume関数に渡されたコールバックを取得
        callback_wrapper = mock_queue.consume.call_args[0][0]
        assert callable(callback_wrapper)


# ユーザー作成レスポンスハンドラーのテスト
@pytest.mark.asyncio
async def test_handle_user_creation_response():
    """
    ユーザー作成レスポンスハンドラーをテスト
    """
    # メッセージモックの作成
    user_id = str(uuid.uuid4())
    message_data = {
        "user_id": user_id,
        "status": "success",
        "message": "User created successfully"
    }
    
    # aio_pikaのメッセージオブジェクトをモック
    mock_message = AsyncMock()
    mock_message.body = json.dumps(message_data).encode()
    mock_message.ack = AsyncMock()
    
    # CRUDオペレーションをモック
    with patch("app.crud.auth_user.auth_user_crud.activate_user") as mock_activate_user, \
         patch("app.core.logging.app_logger.info") as mock_logger_info:
        
        # モックの設定
        mock_activate_user.return_value = True
        
        # ハンドラーを実行
        await handle_user_creation_response(mock_message)
        
        # ユーザーが有効化されたことを確認
        mock_activate_user.assert_called_once()
        args, kwargs = mock_activate_user.call_args
        # データベースセッションと引数をチェック
        assert len(args) >= 2
        assert args[1] == user_id
        
        # メッセージが確認されたことを確認
        mock_message.ack.assert_called_once()
        
        # ログが記録されたことを確認
        mock_logger_info.assert_called()


# 失敗したユーザー作成レスポンスのテスト
@pytest.mark.asyncio
async def test_handle_user_creation_response_failure():
    """
    失敗したユーザー作成レスポンスの処理をテスト
    """
    # 失敗メッセージモックの作成
    user_id = str(uuid.uuid4())
    message_data = {
        "user_id": user_id,
        "status": "failure",
        "message": "Failed to create user"
    }
    
    # aio_pikaのメッセージオブジェクトをモック
    mock_message = AsyncMock()
    mock_message.body = json.dumps(message_data).encode()
    mock_message.ack = AsyncMock()
    
    # CRUDオペレーションとロガーをモック
    with patch("app.crud.auth_user.auth_user_crud.delete_by_user_id") as mock_delete_user, \
         patch("app.core.logging.app_logger.warning") as mock_logger_warning:
        
        # モックの設定
        mock_delete_user.return_value = True
        
        # ハンドラーを実行
        await handle_user_creation_response(mock_message)
        
        # ユーザーが削除されたことを確認
        mock_delete_user.assert_called_once()
        args, kwargs = mock_delete_user.call_args
        # データベースセッションと引数をチェック
        assert len(args) >= 2
        assert args[1] == user_id
        
        # メッセージが確認されたことを確認
        mock_message.ack.assert_called_once()
        
        # 警告ログが記録されたことを確認
        mock_logger_warning.assert_called()


# 無効なメッセージ形式のテスト
@pytest.mark.asyncio
async def test_handle_user_creation_response_invalid_message():
    """
    無効なメッセージ形式の処理をテスト
    """
    # 無効なJSONデータ
    invalid_json = b"{invalid: json"
    
    # aio_pikaのメッセージオブジェクトをモック
    mock_message = AsyncMock()
    mock_message.body = invalid_json
    mock_message.ack = AsyncMock()
    
    # ロガーをモック
    with patch("app.core.logging.app_logger.error") as mock_logger_error:
        
        # ハンドラーを実行
        await handle_user_creation_response(mock_message)
        
        # エラーがログに記録されたことを確認
        mock_logger_error.assert_called()
        
        # メッセージが確認されたことを確認
        mock_message.ack.assert_called_once()


# 必要なフィールドがないメッセージのテスト
@pytest.mark.asyncio
async def test_handle_user_creation_response_missing_fields():
    """
    必要なフィールドがないメッセージの処理をテスト
    """
    # user_idフィールドが欠落したメッセージ
    message_data = {
        "status": "success",
        "message": "User created successfully"
    }
    
    # aio_pikaのメッセージオブジェクトをモック
    mock_message = AsyncMock()
    mock_message.body = json.dumps(message_data).encode()
    mock_message.ack = AsyncMock()
    
    # ロガーをモック
    with patch("app.core.logging.app_logger.error") as mock_logger_error:
        
        # ハンドラーを実行
        await handle_user_creation_response(mock_message)
        
        # エラーがログに記録されたことを確認
        mock_logger_error.assert_called()
        
        # メッセージが確認されたことを確認
        mock_message.ack.assert_called_once()


# データベース操作中に例外が発生した場合のテスト
@pytest.mark.asyncio
async def test_handle_user_creation_response_db_exception():
    """
    データベース操作中に例外が発生した場合の処理をテスト
    """
    # メッセージモックの作成
    user_id = str(uuid.uuid4())
    message_data = {
        "user_id": user_id,
        "status": "success",
        "message": "User created successfully"
    }
    
    # aio_pikaのメッセージオブジェクトをモック
    mock_message = AsyncMock()
    mock_message.body = json.dumps(message_data).encode()
    mock_message.ack = AsyncMock()
    
    # CRUDオペレーションをモックし、例外を発生させる
    with patch("app.crud.auth_user.auth_user_crud.activate_user", 
               side_effect=Exception("Database error")), \
         patch("app.core.logging.app_logger.error") as mock_logger_error:
        
        # ハンドラーを実行
        await handle_user_creation_response(mock_message)
        
        # エラーがログに記録されたことを確認
        mock_logger_error.assert_called()
        
        # メッセージが確認されたことを確認
        mock_message.ack.assert_called_once()
