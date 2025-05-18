import pytest
import uuid
from sqlalchemy.exc import SQLAlchemyError
from pydantic import EmailStr

from app.crud.auth_user import auth_user_crud
from app.crud.exceptions import (
    UserNotFoundError,
    DatabaseQueryError
)
from app.schemas.auth_user import AuthUserCreateDB, AuthUserUpdate


@pytest.mark.asyncio
async def test_update_with_empty_data(db_session, unique_username, unique_email, unique_password):
    """更新データが空の場合のテスト（usernameもemailも指定しない）"""
    # テスト用のユーザーを作成
    username = unique_username
    email = unique_email
    password = unique_password
    
    user_in = AuthUserCreateDB(
        username=username,
        email=email,
        password=password,
        user_id=uuid.uuid4()
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    
    # 空の更新データを作成
    empty_update = AuthUserUpdate()
    
    # 空のデータで更新を試みる - IDを使用
    updated_user_by_id = await auth_user_crud.update_by_id(db_session, created_user.id, empty_update)
    
    # 何も変更されていないことを確認
    assert updated_user_by_id.username == username
    assert updated_user_by_id.email == email
    
    # 空のデータで更新を試みる - ユーザー名を使用
    updated_user_by_username = await auth_user_crud.update_by_username(db_session, username, empty_update)
    
    # 何も変更されていないことを確認
    assert updated_user_by_username.username == username
    assert updated_user_by_username.email == email
    
    # 後片付け
    await auth_user_crud.delete_by_id(db_session, created_user.id)


@pytest.mark.asyncio
async def test_get_all_database_query_error(db_session, monkeypatch):
    """get_allメソッドのデータベースクエリエラー処理をテスト"""
    # SQLAlchemyのセッションのexecuteメソッドをモックして例外を発生させる
    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError("Database query failed")
    
    # セッションのexecuteメソッドをモックに置き換え
    monkeypatch.setattr(db_session, "execute", mock_execute)
    
    # エラーが適切に処理されることを確認
    with pytest.raises(DatabaseQueryError) as exc_info:
        await auth_user_crud.get_all(db_session)
    
    # エラーメッセージを確認
    assert "Failed to retrieve all users" in str(exc_info.value)
    assert "Database query failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_multiple_operations_in_single_transaction(db_session):
    """単一トランザクション内での複数の操作をテスト"""
    # テスト用のユーザーデータを準備
    username1 = f"transuser1{uuid.uuid4().hex[:8]}"
    email1 = f"trans_user1_{uuid.uuid4().hex[:8]}@example.com"
    password1 = "password123"

    username2 = f"transuser2{uuid.uuid4().hex[:8]}"
    email2 = f"trans_user2_{uuid.uuid4().hex[:8]}@example.com"
    password2 = "password456"
    
    # 1. 最初のユーザーを作成
    user_in1 = AuthUserCreateDB(
        username=username1,
        email=email1,
        password=password1,
        user_id=uuid.uuid4()
    )
    created_user1 = await auth_user_crud.create(db_session, user_in1)
    
    # 2. 同じトランザクション内で2番目のユーザーを作成
    user_in2 = AuthUserCreateDB(
        username=username2,
        email=email2,
        password=password2,
        user_id=uuid.uuid4()
    )
    created_user2 = await auth_user_crud.create(db_session, user_in2)
    
    # 3. 同じトランザクション内で1番目のユーザーを更新
    update_data = AuthUserUpdate(username=f"updated{username1}")
    updated_user = await auth_user_crud.update_by_id(db_session, created_user1.id, update_data)
    
    # 4. 変更をコミット
    await db_session.commit()
    
    # 5. 変更が反映されていることを確認
    # 更新されたユーザーの確認
    retrieved_user1 = await auth_user_crud.get_by_id(db_session, created_user1.id)
    assert retrieved_user1.username == f"updated{username1}"
    
    # 2番目のユーザーの確認
    retrieved_user2 = await auth_user_crud.get_by_id(db_session, created_user2.id)
    assert retrieved_user2.username == username2
    
    # 後片付け
    await auth_user_crud.delete_by_id(db_session, created_user1.id)
    await auth_user_crud.delete_by_id(db_session, created_user2.id)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_with_edge_user_id_values(db_session):
    """user_idにエッジケースの値を使用してユーザーを作成するテスト"""
    # テスト用のユーザーデータを準備（基本情報）
    username = f"edgeuser{uuid.uuid4().hex[:8]}"
    email = f"edge_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    
    # UUIDの特殊ケース: すべてゼロのUUID
    zero_uuid = uuid.UUID('00000000-0000-0000-0000-000000000000')
    
    # ゼロUUIDでユーザーを作成
    user_in = AuthUserCreateDB(
        username=username,
        email=email,
        password=password,
        user_id=zero_uuid
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    
    # ユーザーが正しく作成されたことを確認
    assert created_user.username == username
    assert created_user.email == email
    assert created_user.user_id == zero_uuid
    
    # user_idで取得できることを確認
    retrieved_user = await auth_user_crud.get_by_user_id(db_session, zero_uuid)
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == username
    
    # 後片付け
    await auth_user_crud.delete_by_id(db_session, created_user.id)
    await db_session.commit()


@pytest.mark.asyncio
async def test_update_only_email(db_session, unique_username, unique_email, unique_password):
    """emailのみを更新するテスト（usernameは更新しない）"""
    # テスト用のユーザーを作成
    username = unique_username
    original_email = unique_email
    password = unique_password
    
    user_in = AuthUserCreateDB(
        username=username,
        email=original_email,
        password=password,
        user_id=uuid.uuid4()
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    
    # 新しいメールアドレスを生成
    new_email = f"updated_email_{uuid.uuid4().hex[:8]}@example.com"
    
    # emailのみを更新（usernameはNoneのまま）
    update_data = AuthUserUpdate(email=new_email)
    updated_user = await auth_user_crud.update_by_id(db_session, created_user.id, update_data)
    
    # emailのみが更新され、usernameは変更されていないことを確認
    assert updated_user.email == new_email
    assert updated_user.username == username
    
    # 後片付け
    await auth_user_crud.delete_by_id(db_session, created_user.id)
    await db_session.commit()


@pytest.mark.asyncio
async def test_update_only_username(db_session, unique_username, unique_email, unique_password):
    """usernameのみを更新するテスト（emailは更新しない）"""
    # テスト用のユーザーを作成
    original_username = unique_username
    email = unique_email
    password = unique_password
    
    user_in = AuthUserCreateDB(
        username=original_username,
        email=email,
        password=password,
        user_id=uuid.uuid4()
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    
    # 新しいユーザー名を生成（半角英数字のみ）
    new_username = f"updated{uuid.uuid4().hex[:10]}"
    
    # usernameのみを更新（emailはNoneのまま）
    update_data = AuthUserUpdate(username=new_username)
    updated_user = await auth_user_crud.update_by_id(db_session, created_user.id, update_data)
    
    # usernameのみが更新され、emailは変更されていないことを確認
    assert updated_user.username == new_username
    assert updated_user.email == email
    
    # 後片付け
    await auth_user_crud.delete_by_id(db_session, created_user.id)
    await db_session.commit()


@pytest.mark.asyncio
async def test_logger_usage(db_session, unique_username, unique_email, unique_password, monkeypatch, caplog):
    """ロギング機能が適切に使用されていることをテスト"""
    import logging
    # ロガーのモックを作成
    class MockLogger:
        def __init__(self):
            self.info_messages = []
            self.error_messages = []
            self.warning_messages = []
        
        def info(self, message):
            self.info_messages.append(message)
        
        def error(self, message):
            self.error_messages.append(message)
        
        def warning(self, message):
            self.warning_messages.append(message)
    
    # モックロガーのインスタンスを作成
    mock_logger = MockLogger()
    
    # CRUDAuthUserクラスのロガーをモックに置き換え
    monkeypatch.setattr(auth_user_crud, "logger", mock_logger)
    
    # テスト用のユーザーデータを準備
    username = unique_username
    email = unique_email
    password = unique_password
    user_id = uuid.uuid4()
    
    # ユーザーを作成
    user_in = AuthUserCreateDB(
        username=username,
        email=email,
        password=password,
        user_id=user_id
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    
    # ロガーのinfo呼び出しが行われたことを確認
    create_log_message = f"Creating new user with username: {username} and user_id: {user_id}"
    assert any(create_log_message in msg for msg in mock_logger.info_messages)
    
    # ユーザーを削除してログメッセージを確認
    await auth_user_crud.delete_by_id(db_session, created_user.id)
    
    # 削除のログメッセージを確認
    delete_log_message = f"Deleting user by id: {created_user.id}"
    assert any(delete_log_message in msg for msg in mock_logger.info_messages)
    
    # コミット
    await db_session.commit()


@pytest.mark.asyncio
async def test_nonexistent_user_delete_attempt(db_session):
    """存在しないユーザーの削除試行をテスト"""
    # 存在しない UUID を生成
    nonexistent_id = uuid.uuid4()
    
    # 存在しないユーザーの削除を試みる
    with pytest.raises(UserNotFoundError) as exc_info:
        await auth_user_crud.delete_by_id(db_session, nonexistent_id)
    
    # エラーメッセージに ID が含まれていることを確認
    assert str(nonexistent_id) in str(exc_info.value)
