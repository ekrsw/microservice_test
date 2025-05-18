import pytest
import uuid
from pydantic import EmailStr

from app.crud.auth_user import auth_user_crud
from app.crud.exceptions import UserNotFoundError
from app.schemas.auth_user import AuthUserCreateDB


@pytest.mark.asyncio
async def test_delete_auth_user_by_email_complete(db_session, unique_username, unique_email, unique_password):
    """メールアドレスによるユーザー削除の完全テスト"""
    # テスト用のユーザーを作成
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
    
    # ユーザーが作成されたことを確認
    db_user = await auth_user_crud.get_by_email(db_session, email)
    assert db_user is not None
    assert db_user.id == created_user.id
    
    # メールアドレスを使ってユーザーを削除
    deleted_user = await auth_user_crud.delete_by_email(db_session, email)
    
    # 削除されたユーザーの情報を確認
    assert deleted_user.id == created_user.id
    assert deleted_user.username == username
    assert deleted_user.email == email
    assert deleted_user.user_id == user_id
    
    # 実際にDBから削除されたことを確認（メールアドレスで検索）
    try:
        result = await auth_user_crud.get_by_email(db_session, email)
        assert False, "Expected UserNotFoundError but no exception was raised"
    except UserNotFoundError:
        pass
    
    # IDでも検索できないことを確認
    try:
        result = await auth_user_crud.get_by_id(db_session, created_user.id)
        assert False, "Expected UserNotFoundError but no exception was raised"
    except UserNotFoundError:
        pass
    
    # usernameでも検索できないことを確認
    try:
        result = await auth_user_crud.get_by_username(db_session, username)
        assert False, "Expected UserNotFoundError but no exception was raised"
    except UserNotFoundError:
        pass
    
    # user_idでも検索できないことを確認
    try:
        result = await auth_user_crud.get_by_user_id(db_session, user_id)
        assert False, "Expected UserNotFoundError but no exception was raised"
    except UserNotFoundError:
        pass


@pytest.mark.asyncio
async def test_delete_nonexistent_user_by_email(db_session):
    """存在しないメールアドレスでユーザーを削除しようとした場合のテスト"""
    # 存在しないメールアドレスを生成
    nonexistent_email = f"nonexistent_{uuid.uuid4().hex}@example.com"
    
    # 存在しないメールアドレスでユーザーを削除しようとする
    with pytest.raises(UserNotFoundError) as exc_info:
        await auth_user_crud.delete_by_email(db_session, nonexistent_email)
    
    # エラーメッセージにメールアドレスが含まれていることを確認
    assert nonexistent_email in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_by_email_transaction_commit(db_session):
    """メールアドレスでのユーザー削除後のトランザクションコミットをテスト"""
    # テスト用のユーザーを作成
    username = f"deletetestuser{uuid.uuid4().hex[:8]}"
    email = f"deletetest_{uuid.uuid4().hex[:8]}@example.com"
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
    
    # メールアドレスを使ってユーザーを削除
    await auth_user_crud.delete_by_email(db_session, email)
    
    # コミット
    await db_session.commit()
    
    # 別のセッションを作成して、本当に削除されたか確認
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    # 新しいエンジンとセッションを作成
    engine = create_async_engine(settings.DATABASE_URL)
    TestingSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestingSessionLocal() as new_session:
        # 削除したユーザーを検索
        from sqlalchemy import select
        from app.models.auth_user import AuthUser
        
        result = await new_session.execute(
            select(AuthUser).filter(AuthUser.email == email)
        )
        user = result.scalar_one_or_none()
        
        # ユーザーが見つからないことを確認
        assert user is None, f"User with email {email} should have been deleted"
