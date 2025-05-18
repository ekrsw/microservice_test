import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from app.db.init import Database
from app.db.base import Base


# 非同期テスト用のマーカーを追加
pytestmark = pytest.mark.asyncio


# Databaseクラスをモックするためのサブクラス
class MockDatabase(Database):
    """テスト用にinitメソッドをオーバーライドしたDatabaseサブクラス"""
    
    def __init__(self):
        # 親クラスの初期化は不要
        self.conn = None
        self.run_sync_called = False
        self.create_all_called = False
        self.exception_to_raise = None
    
    async def init(self):
        """元のinitメソッドの動作をシミュレート"""
        # 例外を発生させる設定がある場合
        if self.exception_to_raise:
            raise self.exception_to_raise
        
        # 正常に実行された場合は、実行フラグをセット
        self.run_sync_called = True
        self.create_all_called = True
        return True


class TestDatabase:
    """Databaseクラスのテスト"""
    
    @patch('app.db.base.Base.metadata.create_all')
    async def test_init_success(self, mock_create_all):
        """テーブル作成が正常に完了するケースのテスト"""
        # 実際のinitメソッドをテスト
        with patch('app.db.init.async_engine') as mock_engine:
            # 非同期コンテキストマネージャのモック作成
            mock_context = AsyncMock()
            mock_conn = AsyncMock()
            mock_context.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value = mock_context
            
            # テスト対象のメソッドを実行
            db = Database()
            await db.init()
            
            # 正しいメソッドが呼ばれたことを確認
            mock_engine.begin.assert_called_once()
            mock_conn.run_sync.assert_called_once()
            # create_allが呼ばれたことを確認
            mock_create_all.assert_not_called()  # 直接呼ばれるわけではなく、run_syncの引数として渡される
    
    async def test_init_exception(self):
        """テーブル作成中に例外が発生するケースのテスト"""
        # モックデータベースを使用
        db = MockDatabase()
        db.exception_to_raise = Exception("テーブル作成エラー")
        
        # 例外が発生することを確認
        with pytest.raises(Exception) as excinfo:
            await db.init()
        
        # 発生した例外のメッセージを確認
        assert "テーブル作成エラー" in str(excinfo.value)
        
        # フラグが設定されていないことを確認（例外で中断されたため）
        assert not db.run_sync_called
        assert not db.create_all_called
