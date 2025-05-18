import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from app.core.config import Settings


def test_database_url():
    """DATABASE_URLプロパティが正しく生成されるかテスト"""
    # テスト用の設定値
    test_settings = Settings(
        AUTH_POSTGRES_HOST="test_host",
        AUTH_POSTGRES_INTERNAL_PORT="5432",
        AUTH_POSTGRES_USER="test_user",
        AUTH_POSTGRES_PASSWORD="test_password",
        AUTH_POSTGRES_DB="test_db",
        TZ="Asia/Tokyo",
        AUTH_POSTGRES_EXTERNAL_PORT="5433",
        AUTH_REDIS_EXTERNAL_PORT="6379"
    )
    
    # 期待される結果
    expected_url = (
        "postgresql+asyncpg://"
        "test_user:test_password@"
        "test_host:5432/"
        "test_db"
    )
    
    # 生成されたURLが期待通りか確認
    assert test_settings.DATABASE_URL == expected_url


@pytest.mark.parametrize(
    "password,expected_url",
    [
        (
            "redis_password",
            "redis://:redis_password@test_redis_host:6379/0"
        ),
        (
            None,
            "redis://test_redis_host:6379/0"
        )
    ]
)
def test_auth_redis_url(password, expected_url):
    """AUTH_REDIS_URLプロパティが正しく生成されるかテスト"""
    # テスト用の設定値
    test_settings = Settings(
        AUTH_REDIS_HOST="test_redis_host",
        AUTH_REDIS_PORT="6379",
        AUTH_REDIS_PASSWORD=password,
        AUTH_POSTGRES_HOST="dummy",
        AUTH_POSTGRES_USER="dummy",
        AUTH_POSTGRES_PASSWORD="dummy",
        AUTH_POSTGRES_DB="dummy",
        TZ="Asia/Tokyo",
        AUTH_POSTGRES_EXTERNAL_PORT="5433",
        AUTH_REDIS_EXTERNAL_PORT="6379"
    )
    
    # 生成されたURLが期待通りか確認
    assert test_settings.AUTH_REDIS_URL == expected_url


def test_private_key_from_file():
    """PRIVATE_KEYプロパティがファイルから正しく読み込めるかテスト"""
    # テスト用の一時ファイルを作成
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_file:
        tmp_file.write("TEST_PRIVATE_KEY_CONTENT")
        tmp_file_path = tmp_file.name
    
    try:
        # テスト用の設定値
        test_settings = Settings(
            PRIVATE_KEY_PATH=tmp_file_path,
            AUTH_POSTGRES_HOST="dummy",
            AUTH_POSTGRES_USER="dummy",
            AUTH_POSTGRES_PASSWORD="dummy",
            AUTH_POSTGRES_DB="dummy",
            TZ="Asia/Tokyo",
            AUTH_POSTGRES_EXTERNAL_PORT="5433",
            AUTH_REDIS_EXTERNAL_PORT="6379"
        )
        
        # ファイルから読み込まれた値が期待通りか確認
        assert test_settings.PRIVATE_KEY == "TEST_PRIVATE_KEY_CONTENT"
    finally:
        # テスト終了後に一時ファイルを削除
        os.unlink(tmp_file_path)


def test_private_key_from_env_when_file_not_found():
    """PRIVATE_KEYプロパティがファイルが見つからない場合に環境変数から読み込めるかテスト"""
    # 存在しないファイルパスを指定
    non_existent_path = "/path/to/non/existent/file"
    env_key_value = "ENV_PRIVATE_KEY_CONTENT"
    
    # 環境変数をモック
    with patch.dict(os.environ, {"PRIVATE_KEY": env_key_value}):
        # テスト用の設定値
        test_settings = Settings(
            PRIVATE_KEY_PATH=non_existent_path,
            AUTH_POSTGRES_HOST="dummy",
            AUTH_POSTGRES_USER="dummy",
            AUTH_POSTGRES_PASSWORD="dummy",
            AUTH_POSTGRES_DB="dummy",
            TZ="Asia/Tokyo",
            AUTH_POSTGRES_EXTERNAL_PORT="5433",
            AUTH_REDIS_EXTERNAL_PORT="6379"
        )
        
        # 環境変数から読み込まれた値が期待通りか確認
        assert test_settings.PRIVATE_KEY == env_key_value


def test_public_key_from_file():
    """PUBLIC_KEYプロパティがファイルから正しく読み込めるかテスト"""
    # テスト用の一時ファイルを作成
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_file:
        tmp_file.write("TEST_PUBLIC_KEY_CONTENT")
        tmp_file_path = tmp_file.name
    
    try:
        # テスト用の設定値
        test_settings = Settings(
            PUBLIC_KEY_PATH=tmp_file_path,
            AUTH_POSTGRES_HOST="dummy",
            AUTH_POSTGRES_USER="dummy",
            AUTH_POSTGRES_PASSWORD="dummy",
            AUTH_POSTGRES_DB="dummy",
            TZ="Asia/Tokyo",
            AUTH_POSTGRES_EXTERNAL_PORT="5433",
            AUTH_REDIS_EXTERNAL_PORT="6379"
        )
        
        # ファイルから読み込まれた値が期待通りか確認
        assert test_settings.PUBLIC_KEY == "TEST_PUBLIC_KEY_CONTENT"
    finally:
        # テスト終了後に一時ファイルを削除
        os.unlink(tmp_file_path)


def test_public_key_from_env_when_file_not_found():
    """PUBLIC_KEYプロパティがファイルが見つからない場合に環境変数から読み込めるかテスト"""
    # 存在しないファイルパスを指定
    non_existent_path = "/path/to/non/existent/file"
    env_key_value = "ENV_PUBLIC_KEY_CONTENT"
    
    # 環境変数をモック
    with patch.dict(os.environ, {"PUBLIC_KEY": env_key_value}):
        # テスト用の設定値
        test_settings = Settings(
            PUBLIC_KEY_PATH=non_existent_path,
            AUTH_POSTGRES_HOST="dummy",
            AUTH_POSTGRES_USER="dummy",
            AUTH_POSTGRES_PASSWORD="dummy",
            AUTH_POSTGRES_DB="dummy",
            TZ="Asia/Tokyo",
            AUTH_POSTGRES_EXTERNAL_PORT="5433",
            AUTH_REDIS_EXTERNAL_PORT="6379"
        )
        
        # 環境変数から読み込まれた値が期待通りか確認
        assert test_settings.PUBLIC_KEY == env_key_value
