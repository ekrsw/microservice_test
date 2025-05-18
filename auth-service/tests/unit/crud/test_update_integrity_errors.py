import pytest
import uuid
from unittest.mock import AsyncMock
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.auth_user import auth_user_crud
from app.crud.exceptions import DuplicateUsernameError, DuplicateEmailError, DatabaseIntegrityError
from app.schemas.auth_user import AuthUserCreateDB, AuthUserUpdate


@pytest.mark.asyncio
async def test_update_by_id_with_integrity_error_username(db_session, monkeypatch):
    """
    update_by_idメソッドでユーザー名に関連するIntegrityErrorが発生するケースをテスト
    """
    # テスト用のユーザーを作成
    unique_id = uuid.uuid4().hex[:8]
    username = f"updateuser{unique_id}"
    email = f"update.user.{unique_id}@example.com"
    password = "password123"
    
    # ユーザーを作成
    user_in = AuthUserCreateDB(
        username=username,
        email=email,
        password=password,
        user_id=uuid.uuid4()
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    await db_session.commit()
    
    # flushをモックして特定のIntegrityErrorを発生させる
    original_flush = db_session.flush
    
    async def mock_flush(*args, **kwargs):
        error = IntegrityError(None, None, None)
        error.orig = "Duplicate username constraint violation"
        raise error
    
    # セッションのflushをモック
    monkeypatch.setattr(db_session, "flush", mock_flush)
    
    # テスト実行と例外検証
    update_data = AuthUserUpdate(username="newusername")
    with pytest.raises(DuplicateUsernameError) as exc_info:
        await auth_user_crud.update_by_id(db_session, created_user.id, update_data)
    
    # エラーメッセージの検証
    assert "Username already exists" in str(exc_info.value)
    
    # モックを元に戻す
    monkeypatch.setattr(db_session, "flush", original_flush)
    
    # 後片付け：ユーザーを削除
    await db_session.delete(created_user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_update_by_id_with_integrity_error_email(db_session, monkeypatch):
    """
    update_by_idメソッドでメールアドレスに関連するIntegrityErrorが発生するケースをテスト
    """
    # テスト用のユーザーを作成
    unique_id = uuid.uuid4().hex[:8]
    username = f"updateemail{unique_id}"
    email = f"update.email.{unique_id}@example.com"
    password = "password123"
    
    # ユーザーを作成
    user_in = AuthUserCreateDB(
        username=username,
        email=email,
        password=password,
        user_id=uuid.uuid4()
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    await db_session.commit()
    
    # flushをモックして特定のIntegrityErrorを発生させる
    original_flush = db_session.flush
    
    async def mock_flush(*args, **kwargs):
        error = IntegrityError(None, None, None)
        error.orig = "Duplicate email constraint violation"
        raise error
    
    # セッションのflushをモック
    monkeypatch.setattr(db_session, "flush", mock_flush)
    
    # テスト実行と例外検証
    update_data = AuthUserUpdate(email="new.email@example.com")
    with pytest.raises(DuplicateEmailError) as exc_info:
        await auth_user_crud.update_by_id(db_session, created_user.id, update_data)
    
    # エラーメッセージの検証
    assert "Email already exists" in str(exc_info.value)
    
    # モックを元に戻す
    monkeypatch.setattr(db_session, "flush", original_flush)
    
    # 後片付け：ユーザーを削除
    await db_session.delete(created_user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_update_by_id_with_general_integrity_error(db_session, monkeypatch):
    """
    update_by_idメソッドでキーワードを含まない一般的なIntegrityErrorが発生するケースをテスト
    """
    # テスト用のユーザーを作成
    unique_id = uuid.uuid4().hex[:8]
    username = f"updategeneral{unique_id}"
    email = f"update.general.{unique_id}@example.com"
    password = "password123"
    
    # ユーザーを作成
    user_in = AuthUserCreateDB(
        username=username,
        email=email,
        password=password,
        user_id=uuid.uuid4()
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    await db_session.commit()
    
    # flushをモックして特定のIntegrityErrorを発生させる
    original_flush = db_session.flush
    
    async def mock_flush(*args, **kwargs):
        error = IntegrityError(None, None, None)
        error.orig = "General database constraint violation"
        raise error
    
    # セッションのflushをモック
    monkeypatch.setattr(db_session, "flush", mock_flush)
    
    # テスト実行と例外検証
    update_data = AuthUserUpdate(username="newgeneralname")
    with pytest.raises(DatabaseIntegrityError) as exc_info:
        await auth_user_crud.update_by_id(db_session, created_user.id, update_data)
    
    # エラーメッセージの検証
    assert "Database integrity error" in str(exc_info.value)
    
    # モックを元に戻す
    monkeypatch.setattr(db_session, "flush", original_flush)
    
    # 後片付け：ユーザーを削除
    await db_session.delete(created_user)
    await db_session.commit()
