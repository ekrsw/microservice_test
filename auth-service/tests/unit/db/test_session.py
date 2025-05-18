import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import logging

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.engine.url import URL

from app.db.session import async_engine, AsyncSessionLocal, get_async_session
from app.core.config import settings


class TestSessionSetup:
    """セッション設定のテスト"""
    
    def test_async_engine_setup(self):
        """async_engineが正しく設定されていることを確認"""
        # URLの直接比較は避け、可能であればURLのコンポーネントで検証
        try:
            url_components = async_engine.url.translate_connect_args()
            assert url_components['host'] == 'auth-db'
            assert url_components['port'] == 5432
            assert url_components['database'] == 'my_database'
            assert url_components['username'] == 'my_user'
        except (AttributeError, KeyError):
            # 古いバージョンのSQLAlchemyでは異なる方法で検証
            assert 'auth-db' in str(async_engine.url)
            assert '5432' in str(async_engine.url)
            assert 'my_database' in str(async_engine.url)
        
        # エコーモードの検証
        assert async_engine.echo == settings.SQLALCHEMY_ECHO
    
    def test_async_session_local_setup(self):
        """AsyncSessionLocalが正しく設定されていることを確認"""
        # セッションメーカーの基本的な特性を検証
        assert callable(AsyncSessionLocal)  # 呼び出し可能であること
        
        # AsyncSessionの型を直接使わずにクラス名で確認
        assert AsyncSessionLocal.class_.__name__ == 'AsyncSession'
        
        # セッションファクトリの設定を確認
        assert "bind" in AsyncSessionLocal.kw
        assert AsyncSessionLocal.kw["bind"] is async_engine


# 非同期テスト用のマーカー
@pytest.mark.asyncio
class TestGetAsyncSession:
    """get_async_session関数のテスト"""
    
    async def test_get_async_session_normal(self):
        """正常系：セッションが正常に作成、コミット、クローズされる"""
        # セッションモックの作成
        mock_session = AsyncMock(spec=AsyncSession)
        
        # コンテキストマネージャをモック化
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        
        # AsyncSessionLocalをモック化
        with patch('app.db.session.AsyncSessionLocal', return_value=mock_session_ctx), \
             patch('app.db.session.logger') as mock_logger:
            
            # get_async_sessionの実行
            session_generator = get_async_session()
            session = await session_generator.__anext__()
            
            # セッションが正しく取得できたか確認
            assert session == mock_session
            
            # コンテキストマネージャが正しく使用されたか確認
            mock_session_ctx.__aenter__.assert_called_once()
            
            # ログメッセージが出力されたか確認
            mock_logger.debug.assert_any_call("Creating new database session")
            mock_logger.debug.assert_any_call("Database session created successfully")
            
            # ジェネレータの終了処理を実行（finallyブロックをテスト）
            try:
                await session_generator.__anext__()
            except StopAsyncIteration:
                pass
            
            # コミットとクローズが呼ばれたか確認
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
            
            # コミット・クローズ時のログ出力を確認
            mock_logger.debug.assert_any_call("Committing database session")
            mock_logger.debug.assert_any_call("Database session committed successfully")
            mock_logger.debug.assert_any_call("Closing database session")
    
    async def test_get_async_session_exception(self):
        """例外発生ケース：セッション中に例外が発生した場合のロールバック処理"""
        # セッションモックの作成
        mock_session = AsyncMock(spec=AsyncSession)
        
        # コンテキストマネージャをモック化
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        
        # テスト用の例外
        test_exception = Exception("Test session exception")
        
        # AsyncSessionLocalをモック化
        with patch('app.db.session.AsyncSessionLocal', return_value=mock_session_ctx), \
             patch('app.db.session.logger') as mock_logger:
            
            # get_async_sessionの実行
            session_generator = get_async_session()
            session = await session_generator.__anext__()
            
            # 例外を発生させる
            with pytest.raises(Exception) as excinfo:
                # ジェネレータに例外を送信
                await session_generator.athrow(test_exception)
            
            # 送信した例外と同じ例外が再スローされたか確認
            assert excinfo.value == test_exception
            
            # ロールバックが呼ばれたか確認
            mock_session.rollback.assert_called_once()
            
            # エラーログが出力されたか確認
            mock_logger.error.assert_any_call(f"Exception occurred during database session, rolling back: {str(test_exception)}")
            
            # ジェネレータの終了処理を確認（finallyブロックを実行）
            try:
                await session_generator.__anext__()
            except StopAsyncIteration:
                pass
            
            # 例外後もクローズが呼ばれたか確認
            mock_session.close.assert_called_once()
            mock_logger.debug.assert_any_call("Closing database session")
    
    async def test_get_async_session_commit_error(self):
        """コミット失敗ケース：コミット中に例外が発生した場合の処理"""
        # セッションモックの作成
        mock_session = AsyncMock(spec=AsyncSession)
        
        # コミット時に例外を発生させる
        commit_exception = Exception("Commit failed")
        mock_session.commit.side_effect = commit_exception
        
        # コンテキストマネージャをモック化
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        
        # AsyncSessionLocalをモック化
        with patch('app.db.session.AsyncSessionLocal', return_value=mock_session_ctx), \
             patch('app.db.session.logger') as mock_logger:
            
            # get_async_sessionの実行
            session_generator = get_async_session()
            session = await session_generator.__anext__()
            
            # ジェネレータの終了処理（コミットエラー）
            with pytest.raises(Exception) as excinfo:
                try:
                    await session_generator.__anext__()
                except StopAsyncIteration:
                    pass
            
            # コミットの例外が再スローされたか確認
            assert excinfo.value == commit_exception
            
            # エラーログが出力されたか確認
            mock_logger.error.assert_any_call(f"Failed to commit database session: {str(commit_exception)}")
            
            # 例外後もクローズが呼ばれたか確認
            mock_session.close.assert_called_once()
            mock_logger.debug.assert_any_call("Closing database session")
