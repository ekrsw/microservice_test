import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError

# 非同期テスト用のマーカーを追加
pytestmark = pytest.mark.asyncio

from app.core.redis import (
    get_redis_pool,
    save_password_to_redis,
    get_password_from_redis,
    delete_password_from_redis
)
from app.core.config import settings


class TestGetRedisPool:
    """get_redis_pool関数のテスト"""
    
    @patch("app.core.redis._redis", None)  # テスト間で_redisがリセットされるようにする
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_redis_pool_initialization(self, mock_from_url):
        """Redisプール初期化のテスト"""
        # Redisモックの設定
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        # 初回のプール取得
        redis_pool = await get_redis_pool()
        
        # Redis.from_urlが正しいパラメータで呼ばれたことを確認
        mock_from_url.assert_called_once_with(
            settings.AUTH_REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # 返されたプールが正しいことを確認
        assert redis_pool is mock_redis
    
    @patch("app.core.redis._redis", None)  # テスト間で_redisがリセットされるようにする
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_redis_pool_reuse(self, mock_from_url):
        """Redisプール再利用のテスト"""
        # Redisモックの設定
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        # 初回のプール取得
        first_pool = await get_redis_pool()
        
        # 2回目のプール取得
        second_pool = await get_redis_pool()
        
        # Redis.from_urlが1回だけ呼ばれたことを確認
        mock_from_url.assert_called_once()
        
        # 同じインスタンスが返されたことを確認
        assert first_pool is second_pool
    
    @patch("app.core.redis._redis", None)  # テスト間で_redisがリセットされるようにする
    @patch("redis.asyncio.Redis.from_url")
    async def test_get_redis_pool_connection_error(self, mock_from_url):
        """Redisプール接続エラーのテスト"""
        # 接続エラーをシミュレート
        mock_from_url.side_effect = ConnectionError("接続エラー")
        
        # 例外が発生することを確認
        with pytest.raises(ConnectionError):
            await get_redis_pool()


class TestSavePasswordToRedis:
    """save_password_to_redis関数のテスト"""
    
    @patch("time.time")
    @patch("app.core.redis.get_redis_pool")
    async def test_save_password_success(self, mock_get_redis_pool, mock_time):
        """パスワードの保存成功テスト"""
        # タイムスタンプをモック
        mock_time.return_value = 1234567890
        
        # Redisモックの設定
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        mock_get_redis_pool.return_value = mock_redis
        
        # テストパラメータ
        username = "testuser"
        password = "testpassword"
        ttl = 300
        
        # 関数実行
        key = await save_password_to_redis(username, password, ttl)
        
        # 期待されるキー
        expected_key = f"temp_password:{username}:1234567890"
        
        # setexが正しく呼ばれたか確認
        mock_redis.setex.assert_called_once_with(expected_key, ttl, password)
        
        # 返されたキーが正しいか確認
        assert key == expected_key
    
    @patch("time.time")
    @patch("app.core.redis.get_redis_pool")
    async def test_save_password_with_default_ttl(self, mock_get_redis_pool, mock_time):
        """デフォルトTTLでのパスワード保存テスト"""
        # タイムスタンプをモック
        mock_time.return_value = 1234567890
        
        # Redisモックの設定
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        mock_get_redis_pool.return_value = mock_redis
        
        # テストパラメータ
        username = "testuser"
        password = "testpassword"
        # ttlはデフォルトの300を使用
        
        # 関数実行
        await save_password_to_redis(username, password)
        
        # 期待されるキー
        expected_key = f"temp_password:{username}:1234567890"
        
        # setexが正しく呼ばれたか確認（デフォルトTTL）
        mock_redis.setex.assert_called_once_with(expected_key, 300, password)
    
    @patch("time.time")
    @patch("app.core.redis.get_redis_pool")
    async def test_save_password_redis_error(self, mock_get_redis_pool, mock_time):
        """Redisエラー時のパスワード保存テスト"""
        # タイムスタンプをモック
        mock_time.return_value = 1234567890
        
        # Redisエラーをシミュレート
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(side_effect=RedisError("Redis操作エラー"))
        mock_get_redis_pool.return_value = mock_redis
        
        # テストパラメータ
        username = "testuser"
        password = "testpassword"
        
        # 例外が発生することを確認
        with pytest.raises(RedisError):
            await save_password_to_redis(username, password)


class TestGetPasswordFromRedis:
    """get_password_from_redis関数のテスト"""
    
    @patch("app.core.redis.get_redis_pool")
    async def test_get_password_success(self, mock_get_redis_pool):
        """パスワードの取得成功テスト"""
        # テストデータ
        test_key = "temp_password:testuser:1234567890"
        test_password = "testpassword"
        
        # Redisモックの設定
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=test_password)
        mock_get_redis_pool.return_value = mock_redis
        
        # 関数実行
        password = await get_password_from_redis(test_key)
        
        # getが正しく呼ばれたか確認
        mock_redis.get.assert_called_once_with(test_key)
        
        # 返されたパスワードが正しいか確認
        assert password == test_password
    
    @patch("app.core.redis.get_redis_pool")
    async def test_get_password_key_not_found(self, mock_get_redis_pool):
        """存在しないキーからのパスワード取得テスト"""
        # テストキー
        test_key = "temp_password:testuser:1234567890"
        
        # キーが存在しない場合をシミュレート
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_get_redis_pool.return_value = mock_redis
        
        # 関数実行
        password = await get_password_from_redis(test_key)
        
        # getが正しく呼ばれたか確認
        mock_redis.get.assert_called_once_with(test_key)
        
        # 返された値がNoneであることを確認
        assert password is None
    
    @patch("app.core.redis.get_redis_pool")
    async def test_get_password_redis_error(self, mock_get_redis_pool):
        """Redisエラー時のパスワード取得テスト"""
        # テストキー
        test_key = "temp_password:testuser:1234567890"
        
        # Redisエラーをシミュレート
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=RedisError("Redis操作エラー"))
        mock_get_redis_pool.return_value = mock_redis
        
        # 関数実行（エラー時はNoneを返す仕様）
        password = await get_password_from_redis(test_key)
        
        # getが正しく呼ばれたか確認
        mock_redis.get.assert_called_once_with(test_key)
        
        # エラー時はNoneが返されることを確認
        assert password is None


class TestDeletePasswordFromRedis:
    """delete_password_from_redis関数のテスト"""
    
    @patch("app.core.redis.get_redis_pool")
    async def test_delete_password_success(self, mock_get_redis_pool):
        """パスワードの削除成功テスト"""
        # テストキー
        test_key = "temp_password:testuser:1234567890"
        
        # 削除成功をシミュレート（1を返す）
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        mock_get_redis_pool.return_value = mock_redis
        
        # 関数実行
        result = await delete_password_from_redis(test_key)
        
        # deleteが正しく呼ばれたか確認
        mock_redis.delete.assert_called_once_with(test_key)
        
        # 成功時はTrueが返されることを確認
        assert result is True
    
    @patch("app.core.redis.get_redis_pool")
    async def test_delete_password_key_not_found(self, mock_get_redis_pool):
        """存在しないキーの削除テスト"""
        # テストキー
        test_key = "temp_password:testuser:1234567890"
        
        # キーが存在しない場合をシミュレート（0を返す）
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=0)
        mock_get_redis_pool.return_value = mock_redis
        
        # 関数実行
        result = await delete_password_from_redis(test_key)
        
        # deleteが正しく呼ばれたか確認
        mock_redis.delete.assert_called_once_with(test_key)
        
        # キーが存在しない場合はFalseが返されることを確認
        assert result is False
    
    @patch("app.core.redis.get_redis_pool")
    async def test_delete_password_redis_error(self, mock_get_redis_pool):
        """Redisエラー時のパスワード削除テスト"""
        # テストキー
        test_key = "temp_password:testuser:1234567890"
        
        # Redisエラーをシミュレート
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(side_effect=RedisError("Redis操作エラー"))
        mock_get_redis_pool.return_value = mock_redis
        
        # 関数実行
        result = await delete_password_from_redis(test_key)
        
        # deleteが正しく呼ばれたか確認
        mock_redis.delete.assert_called_once_with(test_key)
        
        # エラー時はFalseが返されることを確認
        assert result is False
