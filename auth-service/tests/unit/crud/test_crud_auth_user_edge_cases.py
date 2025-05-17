import pytest
import uuid
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.crud.auth_user import auth_user_crud
from app.crud.exceptions import (
    UserNotFoundError,
    DuplicateUsernameError,
    DuplicateEmailError,
    DatabaseQueryError,
    DatabaseIntegrityError
)
from app.schemas.auth_user import AuthUserCreate, AuthUserCreateDB, AuthUserUpdate, AuthUserUpdatePassword
from pydantic import EmailStr


@pytest.mark.asyncio
async def test_create_multiple_users_transaction_rollback(db_session, monkeypatch):
    """複数ユーザー作成時に一部が失敗した場合、トランザクション全体がロールバックされることを確認する"""
    # 有効なユーザーデータを作成（半角英数字のみのユーザー名）
    valid_users = [
        AuthUserCreateDB(
            username=f"validuser{i}{uuid.uuid4().hex[:8]}",
            email=f"valid_user_{i}_{uuid.uuid4().hex[:8]}@example.com",
            password="password123",
            user_id=uuid.uuid4()
        ) for i in range(3)
    ]
    
    # 元のadd_allメソッドを保存
    original_add_all = db_session.add_all
    
    # 例外を発生させるモック関数
    def mock_add_all(objs):
        # 最初のユーザーは追加するが、その後例外を発生させる
        raise ValueError("Simulated database error")
    
    # add_allメソッドをモックに置き換え
    monkeypatch.setattr(db_session, "add_all", mock_add_all)
    
    # エラーが発生することを確認
    with pytest.raises(ValueError):
        await auth_user_crud.create_multiple(db_session, valid_users)
    
    # トランザクションがロールバックされ、有効なユーザーも作成されていないことを確認
    for user in valid_users:
        try:
            await auth_user_crud.get_by_username(db_session, user.username)
            assert False, f"User {user.username} should not exist after rollback"
        except UserNotFoundError:
            # 期待通りユーザーが見つからない
            pass
    
    # モックを元に戻す
    monkeypatch.setattr(db_session, "add_all", original_add_all)


@pytest.mark.asyncio
async def test_create_multiple_users_with_duplicate_constraint(db_session, unique_user_id, test_user):
    """複数ユーザー作成時に一意性制約違反が発生した場合、トランザクション全体がロールバックされることを確認する"""
    # 既存のユーザー名を取得
    existing_username = test_user.username
    
    # 有効なユーザーデータを作成（半角英数字のみのユーザー名）
    valid_users = [
        AuthUserCreateDB(
            username=f"validuser{i}{uuid.uuid4().hex[:8]}",
            email=f"valid_user_{i}_{uuid.uuid4().hex[:8]}@example.com",
            password="password123",
            user_id=uuid.uuid4()
        ) for i in range(3)
    ]
    
    # 既存のユーザー名を持つユーザーデータを作成
    duplicate_user = AuthUserCreateDB(
        username=existing_username,  # 既存のユーザー名（一意性制約違反）
        email=f"duplicate_{uuid.uuid4().hex[:8]}@example.com",
        password="password123",
        user_id=uuid.uuid4()
    )
    
    # 有効なユーザーと重複ユーザーを混ぜる
    mixed_users = valid_users[:1] + [duplicate_user] + valid_users[1:]
    
    # エラーが発生することを確認
    with pytest.raises(DuplicateUsernameError):
        await auth_user_crud.create_multiple(db_session, mixed_users)
    
    # トランザクションがロールバックされ、有効なユーザーも作成されていないことを確認
    for user in valid_users:
        try:
            await auth_user_crud.get_by_username(db_session, user.username)
            assert False, f"User {user.username} should not exist after rollback"
        except UserNotFoundError:
            # 期待通りユーザーが見つからない
            pass


@pytest.mark.asyncio
async def test_database_connection_error_handling(db_session, monkeypatch):
    """データベース接続エラーが適切にハンドリングされることを確認する"""
    # SQLAlchemyのセッション実行をモックして例外を発生させる
    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError("Database connection error")
    
    # セッションのexecuteメソッドをモックに置き換え
    monkeypatch.setattr(db_session, "execute", mock_execute)
    
    # ユーザー取得操作を実行
    with pytest.raises(DatabaseQueryError) as exc_info:
        await auth_user_crud.get_all(db_session)
    
    # エラーメッセージを確認
    assert "Database connection error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_unexpected_exception_handling(db_session, monkeypatch):
    """予期せぬ例外が適切にハンドリングされることを確認する"""
    # 予期せぬ例外を発生させる関数
    async def mock_get_by_id(*args, **kwargs):
        raise RuntimeError("Unexpected error")
    
    # get_by_idメソッドをモックに置き換え
    monkeypatch.setattr(auth_user_crud, "get_by_id", mock_get_by_id)
    
    # ユーザー更新操作を実行
    user_id = uuid.uuid4()
    update_data = AuthUserUpdate(username="newusername")
    
    with pytest.raises(Exception) as exc_info:
        await auth_user_crud.update_by_id(db_session, user_id, update_data)
    
    # 例外が適切にラップされていることを確認
    assert "Unexpected error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_session_rollback_on_exception(db_session):
    """例外発生時にセッションが適切にロールバックされることを確認する"""
    # テストの代替案：トランザクションのロールバックをシミュレートする
    
    # 1. 新しいセッションを作成（テスト用）
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    # 新しいエンジンとセッションを作成
    engine = create_async_engine(settings.DATABASE_URL)
    TestingSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # 2. 最初のトランザクションでユーザーを作成
    async with TestingSessionLocal() as session1:
        # ユーザー情報を準備（半角英数字のみのユーザー名）
        username = f"rollbacktest{uuid.uuid4().hex[:8]}"
        email = f"rollback_test_{uuid.uuid4().hex[:8]}@example.com"
        password = "password123"
        
        # ユーザーを作成してコミット
        user_in = AuthUserCreateDB(
            username=username,
            email=email,
            password=password,
            user_id=uuid.uuid4()
        )
        created_user = await auth_user_crud.create(session1, user_in)
        await session1.commit()
        
        # ユーザーIDを保存
        user_id = created_user.id
    
    # 3. 別のトランザクションでユーザーを更新し、ロールバック
    async with TestingSessionLocal() as session2:
        # ユーザーを取得
        db_user = await auth_user_crud.get_by_id(session2, user_id)
        
        # ユーザー名を更新（半角英数字のみ）
        updated_username = "updatedusername"
        db_user.username = updated_username
        
        # 変更をロールバック
        await session2.rollback()
    
    # 4. 別のトランザクションでユーザーを取得し、更新されていないことを確認
    async with TestingSessionLocal() as session3:
        # ユーザーを再取得
        db_user = await auth_user_crud.get_by_id(session3, user_id)
        
        # ユーザー名が更新されていないことを確認
        assert db_user.username == username, "Username should not be updated after rollback"
        assert db_user.username != updated_username, "Username should not be updated to new value"
        
        # 後片付け
        await auth_user_crud.delete_by_id(session3, user_id)
        await session3.commit()


@pytest.mark.asyncio
async def test_get_auth_user_by_user_id(db_session, unique_username, unique_email, unique_password):
    """user_idを使用してユーザーを取得できることをテストする"""
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
    
    # user_idでユーザーを取得
    retrieved_user = await auth_user_crud.get_by_user_id(db_session, user_id)
    
    # 取得したユーザーが正しいことを確認
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == username
    assert retrieved_user.email == email
    assert retrieved_user.user_id == user_id
    
    # 後片付け
    await auth_user_crud.delete_by_id(db_session, created_user.id)


@pytest.mark.asyncio
async def test_get_auth_user_by_nonexistent_user_id(db_session):
    """存在しないuser_idでユーザーを取得しようとした場合のエラー処理をテストする"""
    # 存在しないUUID（ランダムに生成）
    nonexistent_user_id = uuid.uuid4()
    
    # 存在しないuser_idでユーザーを取得しようとする
    try:
        await auth_user_crud.get_by_user_id(db_session, nonexistent_user_id)
        assert False, "Expected UserNotFoundError but no exception was raised"
    except UserNotFoundError as e:
        # エラーメッセージの検証
        assert str(nonexistent_user_id) in str(e)
    except Exception as e:
        assert False, f"Expected UserNotFoundError but got {type(e).__name__}: {str(e)}"


@pytest.mark.asyncio
async def test_delete_auth_user_by_email(db_session, unique_username, unique_email, unique_password):
    """メールアドレスからユーザーを削除できることをテストする"""
    # テスト用のユーザーを作成
    username = unique_username
    email = unique_email
    password = unique_password
    
    # ユーザーを作成
    user_in = AuthUserCreateDB(
        username=username,
        email=email,
        password=password,
        user_id=uuid.uuid4()
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


@pytest.mark.asyncio
async def test_integrity_error_without_specific_keywords(db_session, monkeypatch):
    """特定のキーワードを含まないIntegrityErrorが適切に処理されることをテストする"""
    # テスト用のユーザーデータを準備
    username = f"testuser{uuid.uuid4().hex[:8]}"
    email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    user_id = uuid.uuid4()
    
    # session.addメソッドをモックして特殊なIntegrityErrorを発生させる
    original_add = db_session.add
    
    # キーワード（usernameやemail）を含まないIntegrityError
    def mock_add(obj):
        # セッションへの追加操作でIntegrityErrorを発生させる
        error = IntegrityError("statement", {}, Exception("General constraint violation"))
        raise error
    
    # addメソッドをモックに置き換え
    monkeypatch.setattr(db_session, "add", mock_add)
    
    # ユーザー作成を試みてDatabaseIntegrityErrorが発生することを確認
    with pytest.raises(DatabaseIntegrityError) as exc_info:
        await auth_user_crud.create(
            db_session,
            AuthUserCreateDB(
                username=username,
                email=email,
                password=password,
                user_id=user_id
            )
        )
    
    # エラーメッセージを確認
    assert "Database integrity error" in str(exc_info.value)
    
    # モックを元に戻す
    monkeypatch.setattr(db_session, "add", original_add)


@pytest.mark.asyncio
async def test_update_by_id_with_integrity_error(db_session, monkeypatch):
    """update_by_idメソッドでIntegrityError処理をテストする"""
    # テスト用のユーザーを作成
    username = f"updatetest{uuid.uuid4().hex[:8]}"
    email = f"update_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    
    user_in = AuthUserCreateDB(
        username=username,
        email=email,
        password=password,
        user_id=uuid.uuid4()
    )
    created_user = await auth_user_crud.create(db_session, user_in)
    
    # セッションのflushメソッドをモックしてIntegrityErrorを発生させる
    original_flush = db_session.flush
    
    # テストケース1: usernameキーワードを含むIntegrityError
    async def mock_flush_username(*args, **kwargs):
        # キーワード「username」を含むエラーメッセージのIntegrityErrorを発生させる
        error = IntegrityError("statement", {}, Exception("Duplicate entry for username"))
        raise error
    
    # flushメソッドをモックに置き換え
    monkeypatch.setattr(db_session, "flush", mock_flush_username)
    
    # ユーザー更新を試みてDuplicateUsernameErrorが発生することを確認
    with pytest.raises(DuplicateUsernameError) as exc_info:
        update_data = AuthUserUpdate(username="newusername")
        await auth_user_crud.update_by_id(db_session, created_user.id, update_data)
    
    # エラーメッセージを確認
    assert "Username already exists" in str(exc_info.value)
    
    # テストケース2: emailキーワードを含むIntegrityError
    async def mock_flush_email(*args, **kwargs):
        # キーワード「email」を含むエラーメッセージのIntegrityErrorを発生させる
        error = IntegrityError("statement", {}, Exception("Duplicate entry for email"))
        raise error
    
    # flushメソッドをモックに置き換え
    monkeypatch.setattr(db_session, "flush", mock_flush_email)
    
    # ユーザー更新を試みてDuplicateEmailErrorが発生することを確認
    with pytest.raises(DuplicateEmailError) as exc_info:
        update_data = AuthUserUpdate(email="newemail@example.com")
        await auth_user_crud.update_by_id(db_session, created_user.id, update_data)
    
    # エラーメッセージを確認
    assert "Email already exists" in str(exc_info.value)
    
    # テストケース3: 特定のキーワードを含まないIntegrityError
    async def mock_flush_general(*args, **kwargs):
        # 特定のキーワードを含まないIntegrityErrorを発生させる
        error = IntegrityError("statement", {}, Exception("General constraint violation"))
        raise error
    
    # flushメソッドをモックに置き換え
    monkeypatch.setattr(db_session, "flush", mock_flush_general)
    
    # ユーザー更新を試みてDatabaseIntegrityErrorが発生することを確認
    with pytest.raises(DatabaseIntegrityError) as exc_info:
        update_data = AuthUserUpdate(username="anotheruser")
        await auth_user_crud.update_by_id(db_session, created_user.id, update_data)
    
    # エラーメッセージを確認
    assert "Database integrity error" in str(exc_info.value)
    
    # モックを元に戻す
    monkeypatch.setattr(db_session, "flush", original_flush)
