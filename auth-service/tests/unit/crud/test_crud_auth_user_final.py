import pytest
import uuid
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.auth_user import auth_user_crud
from app.crud.exceptions import UserNotFoundError
from app.schemas.auth_user import AuthUserCreateDB


@pytest.mark.asyncio
async def test_delete_by_email_direct(db_session: AsyncSession):
    """明示的にEmailStrを使用した削除テスト"""
    # テスト用のユーザーを作成
    unique_id = uuid.uuid4().hex[:8]
    username = f"finaldeletetest{unique_id}"
    email_str = f"final_delete_test_{unique_id}@example.com"
    password = "password123"
    user_id = uuid.uuid4()
    
    # ユーザーを作成
    user_in = AuthUserCreateDB(
        username=username,
        email=email_str,
        password=password,
        user_id=user_id
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    await db_session.commit()
    
    # 作成されたユーザーを確認
    user = await auth_user_crud.get_by_email(db_session, email_str)
    assert user is not None
    assert user.id == created_user.id
    
    # メールアドレスを使用してユーザーを削除
    deleted_user = await auth_user_crud.delete_by_email(db_session, email_str)
    
    # 削除されたユーザーの確認
    assert deleted_user.id == created_user.id
    assert deleted_user.email == email_str
    
    # コミット
    await db_session.commit()
    
    # 削除されたことを確認
    with pytest.raises(UserNotFoundError):
        await auth_user_crud.get_by_email(db_session, email_str)


@pytest.mark.asyncio
async def test_delete_by_email_with_string(db_session: AsyncSession):
    """文字列をEmailStrとして処理する削除テスト"""
    # テスト用のユーザーを作成
    unique_id = uuid.uuid4().hex[:8]
    username = f"stringdeletetest{unique_id}"
    email_str = f"string_delete_test_{unique_id}@example.com"
    password = "password123"
    user_id = uuid.uuid4()
    
    # ユーザーを作成
    user_in = AuthUserCreateDB(
        username=username,
        email=email_str,
        password=password,
        user_id=user_id
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    await db_session.commit()
    
    # 文字列として直接使用して削除
    deleted_user = await auth_user_crud.delete_by_email(db_session, email_str)
    
    # 削除されたユーザーの確認
    assert deleted_user.id == created_user.id
    assert deleted_user.email == email_str
    
    # コミット
    await db_session.commit()
    
    # 削除されたことを確認
    with pytest.raises(UserNotFoundError):
        await auth_user_crud.get_by_email(db_session, email_str)


@pytest.mark.asyncio
async def test_delete_by_email_exception_handling(db_session: AsyncSession, monkeypatch):
    """delete_by_emailでの例外ハンドリングテスト"""
    # テスト用のユーザーを作成
    unique_id = uuid.uuid4().hex[:8]
    username = f"exceptiontest{unique_id}"
    email_str = f"exception_test_{unique_id}@example.com"
    password = "password123"
    user_id = uuid.uuid4()
    
    # ユーザーを作成
    user_in = AuthUserCreateDB(
        username=username,
        email=email_str,
        password=password,
        user_id=user_id
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    
    # get_by_emailをモックして例外を発生させる
    original_get_by_email = auth_user_crud.get_by_email
    
    async def mock_get_by_email(*args, **kwargs):
        # 元のget_by_emailメソッドを呼び出すが、常にUserNotFoundErrorを発生させる
        raise UserNotFoundError(message=f"User with email {kwargs.get('email', args[1])} not found")
    
    # get_by_emailメソッドをモックに置き換え
    monkeypatch.setattr(auth_user_crud, "get_by_email", mock_get_by_email)
    
    # 例外が発生することを確認
    with pytest.raises(UserNotFoundError):
        await auth_user_crud.delete_by_email(db_session, email_str)

    # モックを元に戻す
    monkeypatch.setattr(auth_user_crud, "get_by_email", original_get_by_email)
    await db_session.commit()
