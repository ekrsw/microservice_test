import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from jose import jwt
import json
import uuid

from app.main import app
from app.core.config import settings
from app.schemas.auth_user import AuthUserCreate, AuthUserCreateDB, AuthUserRead
from app.models.auth_user import AuthUser


# TestClientのセットアップ
@pytest.fixture
def test_app():
    """
    FastAPIアプリケーションのテスト用インスタンスを作成
    """
    # 必要な依存関係をモック
    with patch("app.db.init.Database.init", return_value=None), \
         patch("app.messaging.rabbitmq.rabbitmq_client.initialize", return_value=None), \
         patch("app.messaging.rabbitmq.rabbitmq_client.setup_user_creation_response_consumer", return_value=None), \
         patch("app.messaging.rabbitmq.rabbitmq_client.close", return_value=None):
        
        # TestClientを返す
        client = TestClient(app)
        yield client


# 認証ヘルパー
def get_auth_headers(token):
    """
    認証ヘッダーを生成
    """
    return {"Authorization": f"Bearer {token}"}


# モックユーザーの作成
@pytest.fixture
def mock_user():
    """
    テスト用のモックユーザーを作成
    """
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00",
        "user_id": str(uuid.uuid4())
    }


# ユーザー登録エンドポイントのテスト
@patch("app.crud.auth_user.auth_user_crud.create")
@patch("app.messaging.rabbitmq.rabbitmq_client.publish_user_creation")
def test_register_endpoint(mock_publish, mock_create, test_app):
    """
    ユーザー登録エンドポイントが正しく機能するかテスト
    """
    # モックの設定
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Password123!"
    }
    
    # DBに保存されるユーザーオブジェクトをモック
    db_user = MagicMock()
    db_user.id = 1
    db_user.username = user_data["username"]
    db_user.email = user_data["email"]
    db_user.is_active = True
    db_user.created_at = "2023-01-01T00:00:00"
    db_user.updated_at = "2023-01-01T00:00:00"
    db_user.user_id = str(uuid.uuid4())
    
    # CRUD createメソッドの戻り値を設定
    mock_create.return_value = db_user
    # RabbitMQ publish_user_creationメソッドの戻り値を設定
    mock_publish.return_value = True
    
    # テスト実行
    response = test_app.post(
        "/api/v1/auth/register",
        json=user_data
    )
    
    # レスポンスの検証
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]
    assert "password" not in response_data
    
    # モックが呼び出されたことを確認
    mock_create.assert_called_once()
    mock_publish.assert_called_once()


# ユーザー登録エンドポイントでのバリデーションエラーのテスト
def test_register_endpoint_validation_error(test_app):
    """
    ユーザー登録エンドポイントのバリデーションエラーをテスト
    """
    # 不正なデータ（必須フィールドの欠落）
    invalid_data = {
        "username": "newuser",
        # emailフィールドが欠落
        "password": "Password123!"
    }
    
    # テスト実行
    response = test_app.post(
        "/api/v1/auth/register",
        json=invalid_data
    )
    
    # バリデーションエラーのレスポンスを検証
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data


# ログインエンドポイントのテスト
@patch("app.crud.auth_user.auth_user_crud.authenticate")
@patch("app.core.security.create_access_token")
@patch("app.core.security.create_refresh_token")
def test_login_endpoint(mock_create_refresh_token, mock_create_access_token, mock_authenticate, test_app):
    """
    ログインエンドポイントが正しく機能するかテスト
    """
    # モックの設定
    login_data = {
        "username": "testuser",
        "password": "Password123!"
    }
    
    # 認証結果のモック
    db_user = MagicMock()
    db_user.id = 1
    db_user.username = login_data["username"]
    db_user.email = "test@example.com"
    db_user.is_active = True
    db_user.user_id = str(uuid.uuid4())
    
    # モックメソッドの戻り値を設定
    mock_authenticate.return_value = db_user
    mock_create_access_token.return_value = "mock_access_token"
    mock_create_refresh_token.return_value = "mock_refresh_token"
    
    # テスト実行
    response = test_app.post(
        "/api/v1/auth/token",
        data={"username": login_data["username"], "password": login_data["password"]}
    )
    
    # レスポンスの検証
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["access_token"] == "mock_access_token"
    assert response_data["refresh_token"] == "mock_refresh_token"
    assert response_data["token_type"] == "bearer"
    
    # モックが呼び出されたことを確認
    mock_authenticate.assert_called_once_with(None, login_data["username"], login_data["password"])
    mock_create_access_token.assert_called_once()
    mock_create_refresh_token.assert_called_once()


# ログインエンドポイントの認証失敗テスト
@patch("app.crud.auth_user.auth_user_crud.authenticate")
def test_login_endpoint_authentication_failure(mock_authenticate, test_app):
    """
    ログインエンドポイントでの認証失敗をテスト
    """
    # モックの設定
    login_data = {
        "username": "testuser",
        "password": "WrongPassword"
    }
    
    # 認証失敗をモック
    mock_authenticate.return_value = None
    
    # テスト実行
    response = test_app.post(
        "/api/v1/auth/token",
        data={"username": login_data["username"], "password": login_data["password"]}
    )
    
    # 認証失敗のレスポンスを検証
    assert response.status_code == 401
    response_data = response.json()
    assert "detail" in response_data
    assert response_data["detail"] == "Invalid username or password"
    
    # モックが呼び出されたことを確認
    mock_authenticate.assert_called_once()


# トークンリフレッシュエンドポイントのテスト
@patch("app.core.security.verify_refresh_token")
@patch("app.core.security.create_access_token")
def test_refresh_token_endpoint(mock_create_access_token, mock_verify_refresh_token, test_app):
    """
    トークンリフレッシュエンドポイントが正しく機能するかテスト
    """
    # モックの設定
    refresh_data = {
        "refresh_token": "some_refresh_token"
    }
    
    # リフレッシュトークン検証結果のモック
    mock_verify_refresh_token.return_value = "test_user_id"
    mock_create_access_token.return_value = "new_mock_access_token"
    
    # テスト実行
    response = test_app.post(
        "/api/v1/auth/refresh",
        json=refresh_data
    )
    
    # レスポンスの検証
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["access_token"] == "new_mock_access_token"
    assert response_data["token_type"] == "bearer"
    
    # モックが呼び出されたことを確認
    mock_verify_refresh_token.assert_called_once_with(refresh_data["refresh_token"])
    mock_create_access_token.assert_called_once()


# トークンリフレッシュエンドポイントでの失敗テスト
@patch("app.core.security.verify_refresh_token")
def test_refresh_token_endpoint_invalid_token(mock_verify_refresh_token, test_app):
    """
    無効なリフレッシュトークンでのリフレッシュ失敗をテスト
    """
    # モックの設定
    refresh_data = {
        "refresh_token": "invalid_refresh_token"
    }
    
    # 無効なトークン検証をモック
    mock_verify_refresh_token.return_value = None
    
    # テスト実行
    response = test_app.post(
        "/api/v1/auth/refresh",
        json=refresh_data
    )
    
    # レスポンスの検証
    assert response.status_code == 401
    response_data = response.json()
    assert "detail" in response_data
    assert response_data["detail"] == "Invalid refresh token"
    
    # モックが呼び出されたことを確認
    mock_verify_refresh_token.assert_called_once_with(refresh_data["refresh_token"])


# ユーザー情報取得エンドポイントのテスト
@patch("app.api.deps.get_current_user")
@patch("app.crud.auth_user.auth_user_crud.get_by_user_id")
def test_me_endpoint(mock_get_by_user_id, mock_get_current_user, test_app, mock_user):
    """
    現在のユーザー情報取得エンドポイントをテスト
    """
    # モックの設定
    user_id = mock_user["user_id"]
    
    # 認証済みユーザーをモック
    mock_get_current_user.return_value = {"sub": user_id}
    
    # DB上のユーザーをモック
    db_user = MagicMock()
    db_user.id = mock_user["id"]
    db_user.username = mock_user["username"]
    db_user.email = mock_user["email"]
    db_user.is_active = mock_user["is_active"]
    db_user.created_at = mock_user["created_at"]
    db_user.updated_at = mock_user["updated_at"]
    db_user.user_id = user_id
    
    mock_get_by_user_id.return_value = db_user
    
    # テスト実行
    response = test_app.get("/api/v1/auth/me")
    
    # レスポンスの検証
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == mock_user["username"]
    assert response_data["email"] == mock_user["email"]
    assert response_data["user_id"] == user_id
    
    # モックが呼び出されたことを確認
    mock_get_current_user.assert_called_once()
    mock_get_by_user_id.assert_called_once_with(None, user_id)


# ユーザー情報取得エンドポイントでユーザーが見つからない場合のテスト
@patch("app.api.deps.get_current_user")
@patch("app.crud.auth_user.auth_user_crud.get_by_user_id")
def test_me_endpoint_user_not_found(mock_get_by_user_id, mock_get_current_user, test_app):
    """
    ユーザーが見つからない場合のユーザー情報取得エンドポイントをテスト
    """
    # モックの設定
    user_id = str(uuid.uuid4())
    
    # 認証済みユーザーをモック
    mock_get_current_user.return_value = {"sub": user_id}
    
    # ユーザーが見つからないことをモック
    mock_get_by_user_id.return_value = None
    
    # テスト実行
    response = test_app.get("/api/v1/auth/me")
    
    # レスポンスの検証
    assert response.status_code == 404
    response_data = response.json()
    assert "detail" in response_data
    assert response_data["detail"] == "User not found"
    
    # モックが呼び出されたことを確認
    mock_get_current_user.assert_called_once()
    mock_get_by_user_id.assert_called_once_with(None, user_id)


# ログアウトエンドポイントのテスト
@patch("app.api.deps.get_current_user")
@patch("app.core.security.blacklist_token")
@patch("app.core.security.revoke_refresh_token")
def test_logout_endpoint(mock_revoke_refresh, mock_blacklist, mock_get_current_user, test_app):
    """
    ログアウトエンドポイントが正しく機能するかテスト
    """
    # モックの設定
    user_id = str(uuid.uuid4())
    logout_data = {
        "refresh_token": "some_refresh_token"
    }
    
    # 認証済みユーザーをモック
    mock_get_current_user.return_value = {"sub": user_id}
    
    # トークンのブラックリスト登録と無効化をモック
    mock_blacklist.return_value = True
    mock_revoke_refresh.return_value = True
    
    # テスト実行
    response = test_app.post(
        "/api/v1/auth/logout",
        json=logout_data,
        headers=get_auth_headers("mock_token")
    )
    
    # レスポンスの検証
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Successfully logged out"
    
    # モックが呼び出されたことを確認
    mock_get_current_user.assert_called_once()
    mock_blacklist.assert_called_once()
    mock_revoke_refresh.assert_called_once_with(logout_data["refresh_token"])
