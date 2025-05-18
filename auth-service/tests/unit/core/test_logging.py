import json
import logging
import sys
import tempfile
import os
from unittest.mock import patch, MagicMock, call

import pytest
from fastapi import Request
from logging.handlers import RotatingFileHandler

from app.core.logging import (
    RequestIdFilter,
    CustomJsonFormatter,
    get_logger,
    get_request_logger,
    app_logger
)


class TestRequestIdFilter:
    """RequestIdFilterのテスト"""
    
    def test_filter_with_request_id(self):
        """リクエストIDが存在する場合のフィルター処理"""
        # テスト用のログレコードを作成
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.request_id = "test-request-id"
        
        # フィルター処理
        filter_instance = RequestIdFilter()
        result = filter_instance.filter(record)
        
        # フィルターの結果とリクエストIDの確認
        assert result is True
        assert record.request_id == "test-request-id"
    
    def test_filter_without_request_id(self):
        """リクエストIDが存在しない場合のフィルター処理（デフォルト値が設定されるべき）"""
        # テスト用のログレコードを作成
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # フィルター処理
        filter_instance = RequestIdFilter()
        result = filter_instance.filter(record)
        
        # フィルターの結果とデフォルトのリクエストIDの確認
        assert result is True
        assert record.request_id == "no-request-id"


class TestCustomJsonFormatter:
    """CustomJsonFormatterのテスト"""
    
    def test_format_basic(self):
        """基本的なフォーマット処理"""
        # テスト用のログレコードを作成
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.request_id = "test-request-id"
        
        # フォーマット処理
        formatter = CustomJsonFormatter()
        formatted = formatter.format(record)
        
        # JSON文字列をパース
        log_dict = json.loads(formatted)
        
        # 必要なフィールドが含まれているか確認
        assert "timestamp" in log_dict
        assert log_dict["level"] == "INFO"
        assert log_dict["message"] == "Test message"
        assert log_dict["module"] == "test_path"
        assert log_dict["request_id"] == "test-request-id"
        assert log_dict["line"] == 1
    
    def test_format_with_user_id(self):
        """user_idを含むレコードのフォーマット処理"""
        # テスト用のログレコードを作成
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.request_id = "test-request-id"
        record.user_id = "test-user-id"
        
        # フォーマット処理
        formatter = CustomJsonFormatter()
        formatted = formatter.format(record)
        
        # JSON文字列をパース
        log_dict = json.loads(formatted)
        
        # user_idフィールドの確認
        assert log_dict["user_id"] == "test-user-id"
    
    def test_format_with_exception(self):
        """例外情報を含むレコードのフォーマット処理"""
        # 例外を発生させる
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
        
        # テスト用のログレコードを作成
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test_path",
            lineno=1,
            msg="Exception occurred",
            args=(),
            exc_info=exc_info
        )
        record.request_id = "test-request-id"
        
        # フォーマット処理
        formatter = CustomJsonFormatter()
        formatted = formatter.format(record)
        
        # JSON文字列をパース
        log_dict = json.loads(formatted)
        
        # 例外情報フィールドの確認
        assert "exception" in log_dict
        assert "ValueError: Test exception" in log_dict["exception"]


class TestGetLogger:
    """get_logger関数のテスト"""
    
    def setup_method(self):
        """各テスト実行前のセットアップ"""
        # 既存のハンドラーを持つロガーをクリアするためにrootロガーをリセット
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        
        # すべてのロガーをクリア
        logging.Logger.manager.loggerDict.clear()
    
    @patch("app.core.logging.settings")
    def test_get_logger_development(self, mock_settings):
        """開発環境でのロガー取得テスト"""
        # 開発環境用の設定をモック
        mock_settings.ENVIRONMENT = "development"
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.LOG_TO_FILE = False
        
        # ロガーを取得
        logger = get_logger("test_logger")
        
        # ロガーの設定確認
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        
        # フォーマッターの確認（開発環境ではシンプルなフォーマット）
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, logging.Formatter)
        assert "[%(asctime)s]" in handler.formatter._fmt
    
    @patch("app.core.logging.settings")
    def test_get_logger_production(self, mock_settings):
        """本番環境でのロガー取得テスト"""
        # 本番環境用の設定をモック
        mock_settings.ENVIRONMENT = "production"
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.LOG_TO_FILE = False
        
        # ロガーを取得
        logger = get_logger("test_logger")
        
        # ロガーの設定確認
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        
        # フォーマッターの確認（本番環境ではJSON形式）
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, CustomJsonFormatter)
    
    @patch("app.core.logging.settings")
    def test_get_logger_with_file(self, mock_settings):
        """ファイルログが有効な場合のテスト"""
        # 一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            # ファイルログ有効な設定をモック
            log_file_path = os.path.join(temp_dir, "test.log")
            mock_settings.ENVIRONMENT = "development"
            mock_settings.LOG_LEVEL = "INFO"
            mock_settings.LOG_TO_FILE = True
            mock_settings.LOG_FILE_PATH = log_file_path
            
            # ロガーを取得
            logger = get_logger("test_logger")
            
            # ロガーの設定確認
            assert logger.level == logging.INFO
            assert len(logger.handlers) == 2
            
            # ファイルハンドラーの確認
            file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
            assert len(file_handlers) == 1
            assert file_handlers[0].baseFilename == log_file_path
    
    @patch("app.core.logging.settings")
    def test_get_logger_already_configured(self, mock_settings):
        """既に設定済みのロガーを再取得した場合のテスト"""
        # 設定をモック
        mock_settings.ENVIRONMENT = "development"
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.LOG_TO_FILE = False
        
        # 最初のロガー取得
        logger1 = get_logger("test_logger")
        
        # ハンドラー数を記録
        handler_count = len(logger1.handlers)
        
        # 同じ名前のロガーを再取得
        logger2 = get_logger("test_logger")
        
        # 同じロガーインスタンスであることを確認
        assert logger1 is logger2
        
        # ハンドラーが増えていないことを確認（既存のロガーがそのまま返される）
        assert len(logger2.handlers) == handler_count
    
    @patch("app.core.logging.settings")
    def test_get_logger_debug_level(self, mock_settings):
        """DEBUGレベルのロガー取得テスト"""
        # DEBUGレベルの設定をモック
        mock_settings.ENVIRONMENT = "development"
        mock_settings.LOG_LEVEL = "DEBUG"
        mock_settings.LOG_TO_FILE = False
        
        # ロガーを取得
        logger = get_logger("test_logger")
        
        # ログレベルの確認
        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG


class TestGetRequestLogger:
    """get_request_logger関数のテスト"""
    
    @patch("app.core.logging.get_logger")
    def test_get_request_logger_with_request_id(self, mock_get_logger):
        """リクエストIDを持つリクエストでのロガー取得テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # リクエストオブジェクトをモック
        mock_request = MagicMock(spec=Request)
        mock_request.state.request_id = "test-request-id"
        
        # リクエストロガーを取得
        logger_adapter = get_request_logger(mock_request)
        
        # 結果の確認
        assert isinstance(logger_adapter, logging.LoggerAdapter)
        assert logger_adapter.extra["request_id"] == "test-request-id"
        
        # get_loggerが正しく呼び出されたか確認
        mock_get_logger.assert_called_once_with("app.api")
        
        # 親ロガーへの伝播が無効化されているか確認
        assert mock_logger.propagate is False
    
    @patch("app.core.logging.get_logger")
    def test_get_request_logger_without_request_id(self, mock_get_logger):
        """リクエストIDを持たないリクエストでのロガー取得テスト"""
        # モックロガーを設定
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # リクエストIDを持たないリクエストオブジェクトをモック
        mock_request = MagicMock(spec=Request)
        # request_idを持たないstate属性を設定
        mock_state = MagicMock()
        del mock_state.request_id  # request_id属性を持たないようにする
        mock_request.state = mock_state
        
        # リクエストロガーを取得
        logger_adapter = get_request_logger(mock_request)
        
        # 結果の確認
        assert isinstance(logger_adapter, logging.LoggerAdapter)
        assert logger_adapter.extra["request_id"] == "no-request-id"


class TestAppLogger:
    """app_loggerのテスト"""
    
    def test_app_logger_initialization(self):
        """app_loggerの初期化テスト"""
        # app_loggerにアクセス
        from app.core.logging import app_logger
        
        # app_loggerが正しく初期化されているか確認
        assert app_logger is not None
        assert isinstance(app_logger, logging.Logger)
        assert app_logger.name == "app"
