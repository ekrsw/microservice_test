import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException, status
from jose import JWTError
from pydantic import ValidationError
import uuid

from app.api.deps import get_current_user, validate_refresh_token
from app.models.auth_user import AuthUser


# 非同期テスト用のマーカーを追加
pytestmark = pytest.mark.asyncio


class TestGetCurrentUser:
    """get_current_user 依存関数のテスト"""
    
    async def test_get_current_user_success(self):
        """有効なトークンで正常にユーザーを取得するケース"""
        # テスト用のユーザーID
        user_id = str(uuid.uuid4())
        
        # モックのペイロード
        mock_payload = {"user_id": user_id}
        
        # モックのユーザーオブジェクト
        mock_user = MagicMock(spec=AuthUser)
        mock_user.user_id = user_id
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        
        # verify_tokenのモック
        with patch("app.api.deps.verify_token", return_value=mock_payload) as mock_verify_token, \
             patch("app.api.deps.auth_user_crud.get_by_user_id", return_value=mock_user) as mock_get_by_user_id:
            
            # テスト対象の関数を実行
            result = await get_current_user(token="valid_token", async_session=AsyncMock())
            
            # 結果を検証
            assert result == mock_user
            
            # モックが正しく呼び出されたことを確認
            mock_verify_token.assert_called_once_with("valid_token")
            mock_get_by_user_id.assert_called_once()
    
    async def test_get_current_user_invalid_token(self):
        """トークン検証がNoneを返す場合"""
        # verify_tokenのモック（Noneを返す）
        with patch("app.api.deps.verify_token", return_value=None):
            # テスト対象の関数を実行し、例外が発生することを確認
            with pytest.raises(HTTPException) as excinfo:
                await get_current_user(token="invalid_token", async_session=AsyncMock())
            
            # 例外の内容を検証
            assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert excinfo.value.detail == "認証情報が無効です"
            assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}
    
    async def test_get_current_user_missing_user_id(self):
        """ペイロードにuser_idが含まれていない場合"""
        # user_idがないペイロード
        mock_payload = {"some_field": "some_value"}
        
        # verify_tokenのモック
        with patch("app.api.deps.verify_token", return_value=mock_payload):
            # テスト対象の関数を実行し、例外が発生することを確認
            with pytest.raises(HTTPException) as excinfo:
                await get_current_user(token="token_without_user_id", async_session=AsyncMock())
            
            # 例外の内容を検証
            assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert excinfo.value.detail == "認証情報が無効です"
            assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}
    
    async def test_get_current_user_jwt_error(self):
        """JWTErrorが発生する場合"""
        # verify_tokenのモック（JWTErrorを発生させる）
        with patch("app.api.deps.verify_token", side_effect=JWTError("Invalid token")):
            # テスト対象の関数を実行し、例外が発生することを確認
            with pytest.raises(HTTPException) as excinfo:
                await get_current_user(token="invalid_jwt_token", async_session=AsyncMock())
            
            # 例外の内容を検証
            assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert excinfo.value.detail == "認証情報が無効です"
            assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}
    
    async def test_get_current_user_validation_error(self):
        """ValidationErrorが発生する場合"""
        # verify_tokenのモック（ValidationErrorを発生させる）
        with patch("app.api.deps.verify_token", side_effect=ValidationError([], MagicMock())):
            # テスト対象の関数を実行し、例外が発生することを確認
            with pytest.raises(HTTPException) as excinfo:
                await get_current_user(token="invalid_format_token", async_session=AsyncMock())
            
            # 例外の内容を検証
            assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert excinfo.value.detail == "認証情報が無効です"
            assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}
    
    async def test_get_current_user_user_not_found(self):
        """データベースからユーザーが見つからない場合"""
        # テスト用のユーザーID
        user_id = str(uuid.uuid4())
        
        # モックのペイロード
        mock_payload = {"user_id": user_id}
        
        # verify_tokenのモック
        with patch("app.api.deps.verify_token", return_value=mock_payload), \
             patch("app.api.deps.auth_user_crud.get_by_user_id", return_value=None):
            
            # テスト対象の関数を実行し、例外が発生することを確認
            with pytest.raises(HTTPException) as excinfo:
                await get_current_user(token="token_with_invalid_user", async_session=AsyncMock())
            
            # 例外の内容を検証
            assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert excinfo.value.detail == "認証情報が無効です"
            assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}


class TestValidateRefreshToken:
    """validate_refresh_token 関数のテスト"""
    
    async def test_validate_refresh_token_success(self):
        """有効なリフレッシュトークンの検証が成功するケース"""
        # テスト用のユーザーID
        user_id = str(uuid.uuid4())
        refresh_token = "valid_refresh_token"
        
        # verify_refresh_tokenのモック
        with patch("app.api.deps.verify_refresh_token", return_value=user_id) as mock_verify_refresh:
            # テスト対象の関数を実行
            result = await validate_refresh_token(refresh_token)
            
            # 結果を検証
            assert result == user_id
            
            # モックが正しく呼び出されたことを確認
            mock_verify_refresh.assert_called_once_with(refresh_token)
    
    async def test_validate_refresh_token_invalid(self):
        """無効なリフレッシュトークンの場合"""
        refresh_token = "invalid_refresh_token"
        
        # verify_refresh_tokenのモック（Noneを返す）
        with patch("app.api.deps.verify_refresh_token", return_value=None):
            # テスト対象の関数を実行し、例外が発生することを確認
            with pytest.raises(HTTPException) as excinfo:
                await validate_refresh_token(refresh_token)
            
            # 例外の内容を検証
            assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert excinfo.value.detail == "リフレッシュトークンが無効です"
            assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}
