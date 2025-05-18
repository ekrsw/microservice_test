import uuid
import pytest
from pydantic import ValidationError

from app.schemas.auth_user import (
    AuthUserBase,
    AuthUserCreate,
    AuthUserCreateDB,
    AuthUserUpdate,
    AuthUserUpdatePassword,
    AuthUserInDBBase,
    AuthUserResponse,
    Token,
    TokenPayload,
    RefreshTokenRequest,
    LogoutRequest
)


class TestAuthUserBase:
    """AuthUserBaseクラスのテスト"""
    
    def test_auth_user_base_with_valid_data(self):
        """有効なデータでのAuthUserBase初期化テスト"""
        user = AuthUserBase(username="testuser", email="test@example.com")
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_auth_user_base_with_none_values(self):
        """Noneを含むデータでのAuthUserBase初期化テスト"""
        user = AuthUserBase(username=None, email=None)
        assert user.username is None
        assert user.email is None
    
    def test_username_alphanumeric_validator_valid(self):
        """username_alphanumericバリデータの有効ケースのテスト"""
        user = AuthUserBase(username="test123")
        assert user.username == "test123"
    
    def test_username_alphanumeric_validator_with_none(self):
        """username_alphanumericバリデータでNoneが渡された場合のテスト"""
        user = AuthUserBase(username=None)
        assert user.username is None
    
    def test_username_alphanumeric_validator_invalid(self):
        """username_alphanumericバリデータの無効ケースのテスト"""
        with pytest.raises(ValidationError) as excinfo:
            AuthUserBase(username="test-user")  # ハイフンを含む
        assert "ユーザーネームは半角英数字のみ使用可能です" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            AuthUserBase(username="テストユーザー")  # 日本語
        assert "ユーザーネームは半角英数字のみ使用可能です" in str(excinfo.value)


class TestAuthUserCreate:
    """AuthUserCreateクラスのテスト"""
    
    def test_auth_user_create_with_valid_data(self):
        """有効なデータでのAuthUserCreate初期化テスト"""
        user = AuthUserCreate(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"
    
    def test_auth_user_create_with_min_length_username(self):
        """最小長のユーザー名でのAuthUserCreate初期化テスト"""
        user = AuthUserCreate(
            username="abc",  # 3文字
            email="test@example.com",
            password="password123"
        )
        assert user.username == "abc"
    
    def test_auth_user_create_with_too_short_username(self):
        """短すぎるユーザー名での初期化テスト（バリデーションエラー）"""
        with pytest.raises(ValidationError) as excinfo:
            AuthUserCreate(
                username="ab",  # 2文字
                email="test@example.com",
                password="password123"
            )
        assert "String should have at least 3 characters" in str(excinfo.value)
    
    def test_auth_user_create_with_too_long_username(self):
        """長すぎるユーザー名での初期化テスト（バリデーションエラー）"""
        with pytest.raises(ValidationError) as excinfo:
            AuthUserCreate(
                username="a" * 51,  # 51文字
                email="test@example.com",
                password="password123"
            )
        assert "String should have at most 50 characters" in str(excinfo.value)
    
    def test_auth_user_create_with_invalid_email(self):
        """無効なメールアドレスでの初期化テスト（バリデーションエラー）"""
        with pytest.raises(ValidationError) as excinfo:
            AuthUserCreate(
                username="testuser",
                email="invalid-email",  # 無効なメールアドレス
                password="password123"
            )
        assert "value is not a valid email address" in str(excinfo.value)
    
    def test_auth_user_create_with_empty_password(self):
        """空パスワードでの初期化テスト（バリデーションエラー）"""
        with pytest.raises(ValidationError) as excinfo:
            AuthUserCreate(
                username="testuser",
                email="test@example.com",
                password=""  # 空文字
            )
        assert "String should have at least 1 character" in str(excinfo.value)
    
    def test_auth_user_create_with_too_long_password(self):
        """長すぎるパスワードでの初期化テスト（バリデーションエラー）"""
        with pytest.raises(ValidationError) as excinfo:
            AuthUserCreate(
                username="testuser",
                email="test@example.com",
                password="a" * 17  # 17文字
            )
        assert "String should have at most 16 characters" in str(excinfo.value)
    
    def test_password_alphanumeric_validator_valid(self):
        """password_alphanumericバリデータの有効ケースのテスト"""
        user = AuthUserCreate(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        assert user.password == "password123"
    
    def test_password_alphanumeric_validator_invalid(self):
        """password_alphanumericバリデータの無効ケースのテスト"""
        with pytest.raises(ValidationError) as excinfo:
            AuthUserCreate(
                username="testuser",
                email="test@example.com",
                password="password-123"  # ハイフンを含む
            )
        assert "パスワードは半角英数字のみ使用可能です" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            AuthUserCreate(
                username="testuser",
                email="test@example.com",
                password="パスワード123"  # 日本語を含む
            )
        assert "パスワードは半角英数字のみ使用可能です" in str(excinfo.value)
    
    def test_auth_user_create_with_missing_fields(self):
        """必須フィールドが欠けている場合のテスト"""
        with pytest.raises(ValidationError):
            AuthUserCreate(
                email="test@example.com",
                password="password123"
                # usernameが欠けている
            )
        
        with pytest.raises(ValidationError):
            AuthUserCreate(
                username="testuser",
                password="password123"
                # emailが欠けている
            )
        
        with pytest.raises(ValidationError):
            AuthUserCreate(
                username="testuser",
                email="test@example.com"
                # passwordが欠けている
            )


class TestAuthUserCreateDB:
    """AuthUserCreateDBクラスのテスト"""
    
    def test_auth_user_create_db_with_valid_data(self):
        """有効なデータでのAuthUserCreateDB初期化テスト"""
        user_id = uuid.uuid4()
        user = AuthUserCreateDB(
            username="testuser",
            email="test@example.com",
            password="password123",
            user_id=user_id
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.user_id == user_id
    
    def test_auth_user_create_db_without_user_id(self):
        """user_idなしでの初期化テスト（バリデーションエラー）"""
        with pytest.raises(ValidationError) as excinfo:
            AuthUserCreateDB(
                username="testuser",
                email="test@example.com",
                password="password123"
                # user_idが欠けている
            )
        assert "Field required" in str(excinfo.value)


class TestAuthUserUpdate:
    """AuthUserUpdateクラスのテスト"""
    
    def test_auth_user_update_with_all_fields(self):
        """すべてのフィールドが指定されたAuthUserUpdateの初期化テスト"""
        user_id = uuid.uuid4()
        user = AuthUserUpdate(
            username="newusername",
            email="newemail@example.com",
            user_id=user_id
        )
        assert user.username == "newusername"
        assert user.email == "newemail@example.com"
        assert user.user_id == user_id
    
    def test_auth_user_update_with_partial_fields(self):
        """一部のフィールドのみ指定されたAuthUserUpdateの初期化テスト"""
        # usernameのみ
        user1 = AuthUserUpdate(username="newusername")
        assert user1.username == "newusername"
        assert user1.email is None
        assert user1.user_id is None
        
        # emailのみ
        user2 = AuthUserUpdate(email="newemail@example.com")
        assert user2.username is None
        assert user2.email == "newemail@example.com"
        assert user2.user_id is None
        
        # user_idのみ
        user_id = uuid.uuid4()
        user3 = AuthUserUpdate(user_id=user_id)
        assert user3.username is None
        assert user3.email is None
        assert user3.user_id == user_id
    
    def test_auth_user_update_with_empty_data(self):
        """空データでのAuthUserUpdateの初期化テスト"""
        user = AuthUserUpdate()
        assert user.username is None
        assert user.email is None
        assert user.user_id is None
    
    def test_auth_user_update_username_validation(self):
        """ユーザー名のバリデーションテスト"""
        # 短すぎるユーザー名
        with pytest.raises(ValidationError) as excinfo:
            AuthUserUpdate(username="ab")  # 2文字
        assert "String should have at least 3 characters" in str(excinfo.value)
        
        # 長すぎるユーザー名
        with pytest.raises(ValidationError) as excinfo:
            AuthUserUpdate(username="a" * 51)  # 51文字
        assert "String should have at most 50 characters" in str(excinfo.value)
        
        # 無効な文字を含むユーザー名
        with pytest.raises(ValidationError) as excinfo:
            AuthUserUpdate(username="test-user")  # ハイフンを含む
        assert "ユーザーネームは半角英数字のみ使用可能です" in str(excinfo.value)


class TestAuthUserUpdatePassword:
    """AuthUserUpdatePasswordクラスのテスト"""
    
    def test_auth_user_update_password_with_valid_data(self):
        """有効なデータでのAuthUserUpdatePassword初期化テスト"""
        password_update = AuthUserUpdatePassword(
            current_password="oldpassword",
            new_password="newpassword"
        )
        assert password_update.current_password == "oldpassword"
        assert password_update.new_password == "newpassword"
    
    def test_auth_user_update_password_with_invalid_new_password(self):
        """無効な新パスワードでの初期化テスト（バリデーションエラー）"""
        # 長すぎるパスワード
        with pytest.raises(ValidationError) as excinfo:
            AuthUserUpdatePassword(
                current_password="oldpassword",
                new_password="a" * 17  # 17文字
            )
        assert "String should have at most 16 characters" in str(excinfo.value)
        
        # 無効な文字を含むパスワード
        with pytest.raises(ValidationError) as excinfo:
            AuthUserUpdatePassword(
                current_password="oldpassword",
                new_password="new-password"  # ハイフンを含む
            )
        assert "パスワードは半角英数字のみ使用可能です" in str(excinfo.value)
    
    def test_auth_user_update_password_with_missing_fields(self):
        """必須フィールドが欠けている場合のテスト"""
        with pytest.raises(ValidationError):
            AuthUserUpdatePassword(
                new_password="newpassword"
                # current_passwordが欠けている
            )
        
        with pytest.raises(ValidationError):
            AuthUserUpdatePassword(
                current_password="oldpassword"
                # new_passwordが欠けている
            )


class TestAuthUserInDBBase:
    """AuthUserInDBBaseクラスのテスト"""
    
    def test_auth_user_in_db_base_with_valid_data(self):
        """有効なデータでのAuthUserInDBBase初期化テスト"""
        user_id = uuid.uuid4()
        db_id = uuid.uuid4()
        user = AuthUserInDBBase(
            id=db_id,
            username="testuser",
            email="test@example.com",
            user_id=user_id
        )
        assert user.id == db_id
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.user_id == user_id
    
    def test_auth_user_in_db_base_without_user_id(self):
        """user_idなしでの初期化テスト"""
        db_id = uuid.uuid4()
        user = AuthUserInDBBase(
            id=db_id,
            username="testuser",
            email="test@example.com"
        )
        assert user.id == db_id
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.user_id is None
    
    def test_auth_user_in_db_base_with_missing_required_fields(self):
        """必須フィールドが欠けている場合のテスト"""
        db_id = uuid.uuid4()
        
        # usernameが欠けている
        with pytest.raises(ValidationError):
            AuthUserInDBBase(
                id=db_id,
                email="test@example.com"
            )
        
        # emailが欠けている
        with pytest.raises(ValidationError):
            AuthUserInDBBase(
                id=db_id,
                username="testuser"
            )
        
        # idが欠けている
        with pytest.raises(ValidationError):
            AuthUserInDBBase(
                username="testuser",
                email="test@example.com"
            )


class TestAuthUserResponse:
    """AuthUserResponseクラスのテスト"""
    
    def test_auth_user_response_with_valid_data(self):
        """有効なデータでのAuthUserResponse初期化テスト"""
        user_id = uuid.uuid4()
        db_id = uuid.uuid4()
        user = AuthUserResponse(
            id=db_id,
            username="testuser",
            email="test@example.com",
            user_id=user_id
        )
        assert user.id == db_id
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.user_id == user_id


class TestToken:
    """Tokenクラスのテスト"""
    
    def test_token_with_valid_data(self):
        """有効なデータでのToken初期化テスト"""
        token = Token(
            access_token="access_token_value",
            refresh_token="refresh_token_value"
        )
        assert token.access_token == "access_token_value"
        assert token.refresh_token == "refresh_token_value"
        assert token.token_type == "bearer"  # デフォルト値
    
    def test_token_with_custom_token_type(self):
        """カスタムトークンタイプでの初期化テスト"""
        token = Token(
            access_token="access_token_value",
            refresh_token="refresh_token_value",
            token_type="custom"
        )
        assert token.access_token == "access_token_value"
        assert token.refresh_token == "refresh_token_value"
        assert token.token_type == "custom"
    
    def test_token_with_missing_fields(self):
        """必須フィールドが欠けている場合のテスト"""
        with pytest.raises(ValidationError):
            Token(
                refresh_token="refresh_token_value"
                # access_tokenが欠けている
            )
        
        with pytest.raises(ValidationError):
            Token(
                access_token="access_token_value"
                # refresh_tokenが欠けている
            )


class TestTokenPayload:
    """TokenPayloadクラスのテスト"""
    
    def test_token_payload_with_valid_data(self):
        """有効なデータでのTokenPayload初期化テスト"""
        payload = TokenPayload(sub="user_id")
        assert payload.sub == "user_id"
    
    def test_token_payload_with_none(self):
        """サブジェクトがNoneの場合のテスト"""
        payload = TokenPayload(sub=None)
        assert payload.sub is None
    
    def test_token_payload_without_sub(self):
        """サブジェクトを指定しない場合のテスト"""
        payload = TokenPayload()
        assert payload.sub is None


class TestRefreshTokenRequest:
    """RefreshTokenRequestクラスのテスト"""
    
    def test_refresh_token_request_with_valid_data(self):
        """有効なデータでのRefreshTokenRequest初期化テスト"""
        request = RefreshTokenRequest(
            refresh_token="refresh_token_value",
            access_token="access_token_value"
        )
        assert request.refresh_token == "refresh_token_value"
        assert request.access_token == "access_token_value"
    
    def test_refresh_token_request_with_missing_fields(self):
        """必須フィールドが欠けている場合のテスト"""
        with pytest.raises(ValidationError):
            RefreshTokenRequest(
                access_token="access_token_value"
                # refresh_tokenが欠けている
            )
        
        with pytest.raises(ValidationError):
            RefreshTokenRequest(
                refresh_token="refresh_token_value"
                # access_tokenが欠けている
            )


class TestLogoutRequest:
    """LogoutRequestクラスのテスト"""
    
    def test_logout_request_with_valid_data(self):
        """有効なデータでのLogoutRequest初期化テスト"""
        request = LogoutRequest(
            refresh_token="refresh_token_value",
            access_token="access_token_value"
        )
        assert request.refresh_token == "refresh_token_value"
        assert request.access_token == "access_token_value"
    
    def test_logout_request_with_missing_fields(self):
        """必須フィールドが欠けている場合のテスト"""
        with pytest.raises(ValidationError):
            LogoutRequest(
                access_token="access_token_value"
                # refresh_tokenが欠けている
            )
        
        with pytest.raises(ValidationError):
            LogoutRequest(
                refresh_token="refresh_token_value"
                # access_tokenが欠けている
            )
