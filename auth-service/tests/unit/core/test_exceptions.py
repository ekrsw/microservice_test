import pytest
from app.core.exceptions import (
    AppException,
    ResourceNotFoundError,
    ValidationError,
    DuplicateResourceError
)


class TestAppException:
    """AppExceptionクラスのテスト"""
    
    def test_app_exception_default(self):
        """AppExceptionのデフォルトメッセージでの初期化テスト"""
        # 例外を作成
        exception = AppException()
        
        # 期待されるメッセージで初期化されていることを確認
        assert exception.message == "An application error occurred"
        assert str(exception) == "An application error occurred"
    
    def test_app_exception_custom_message(self):
        """AppExceptionのカスタムメッセージでの初期化テスト"""
        # カスタムメッセージで例外を作成
        custom_message = "Custom error message"
        exception = AppException(message=custom_message)
        
        # カスタムメッセージで初期化されていることを確認
        assert exception.message == custom_message
        assert str(exception) == custom_message


class TestResourceNotFoundError:
    """ResourceNotFoundErrorクラスのテスト"""
    
    def test_resource_not_found_error_with_resource_type_only(self):
        """リソースタイプのみでの初期化テスト"""
        # リソースタイプだけで例外を作成
        resource_type = "User"
        exception = ResourceNotFoundError(resource_type=resource_type)
        
        # プロパティと生成されたメッセージの確認
        assert exception.resource_type == resource_type
        assert exception.resource_id is None
        assert exception.message == "User not found"
        assert str(exception) == "User not found"
    
    def test_resource_not_found_error_with_resource_id(self):
        """リソースタイプとIDでの初期化テスト"""
        # リソースタイプとIDで例外を作成
        resource_type = "User"
        resource_id = "123"
        exception = ResourceNotFoundError(resource_type=resource_type, resource_id=resource_id)
        
        # プロパティと生成されたメッセージの確認
        assert exception.resource_type == resource_type
        assert exception.resource_id == resource_id
        assert exception.message == "User not found (id: 123)"
        assert str(exception) == "User not found (id: 123)"
    
    def test_resource_not_found_error_with_custom_message(self):
        """カスタムメッセージでの初期化テスト"""
        # すべてのパラメータで例外を作成
        resource_type = "User"
        resource_id = "123"
        custom_message = "Custom not found message"
        exception = ResourceNotFoundError(
            resource_type=resource_type,
            resource_id=resource_id,
            message=custom_message
        )
        
        # プロパティと指定したカスタムメッセージの確認
        assert exception.resource_type == resource_type
        assert exception.resource_id == resource_id
        assert exception.message == custom_message
        assert str(exception) == custom_message


class TestValidationError:
    """ValidationErrorクラスのテスト"""
    
    def test_validation_error_default(self):
        """バリデーションエラーのデフォルト初期化テスト"""
        # パラメータなしで例外を作成
        exception = ValidationError()
        
        # プロパティとデフォルトメッセージの確認
        assert exception.field is None
        assert exception.details is None
        assert exception.message == "Validation error"
        assert str(exception) == "Validation error"
    
    def test_validation_error_with_field(self):
        """フィールド指定でのバリデーションエラー初期化テスト"""
        # フィールドだけで例外を作成
        field = "username"
        exception = ValidationError(field=field)
        
        # プロパティと生成されたメッセージの確認
        assert exception.field == field
        assert exception.details is None
        assert exception.message == "Validation error for field 'username'"
        assert str(exception) == "Validation error for field 'username'"
    
    def test_validation_error_with_field_and_details(self):
        """フィールドと詳細付きのバリデーションエラー初期化テスト"""
        # フィールドと詳細で例外を作成
        field = "username"
        details = "must be at least 3 characters"
        exception = ValidationError(field=field, details=details)
        
        # プロパティと生成されたメッセージの確認
        assert exception.field == field
        assert exception.details == details
        assert exception.message == "Validation error for field 'username': must be at least 3 characters"
        assert str(exception) == "Validation error for field 'username': must be at least 3 characters"
    
    def test_validation_error_with_custom_message(self):
        """カスタムメッセージでのバリデーションエラー初期化テスト"""
        # すべてのパラメータで例外を作成
        field = "username"
        details = "must be at least 3 characters"
        custom_message = "Custom validation message"
        exception = ValidationError(
            field=field,
            details=details,
            message=custom_message
        )
        
        # プロパティと指定したカスタムメッセージの確認
        assert exception.field == field
        assert exception.details == details
        assert exception.message == custom_message
        assert str(exception) == custom_message


class TestDuplicateResourceError:
    """DuplicateResourceErrorクラスのテスト"""
    
    def test_duplicate_resource_error_with_resource_type_only(self):
        """リソースタイプのみでの重複エラー初期化テスト"""
        # リソースタイプだけで例外を作成
        resource_type = "User"
        exception = DuplicateResourceError(resource_type=resource_type)
        
        # プロパティと生成されたメッセージの確認
        assert exception.resource_type == resource_type
        assert exception.field is None
        assert exception.value is None
        assert exception.message == "Duplicate User"
        assert str(exception) == "Duplicate User"
    
    def test_duplicate_resource_error_with_field_and_value(self):
        """フィールドと値付きでの重複エラー初期化テスト"""
        # リソースタイプ、フィールド、値で例外を作成
        resource_type = "User"
        field = "username"
        value = "testuser"
        exception = DuplicateResourceError(
            resource_type=resource_type,
            field=field,
            value=value
        )
        
        # プロパティと生成されたメッセージの確認
        assert exception.resource_type == resource_type
        assert exception.field == field
        assert exception.value == value
        assert exception.message == "Duplicate User with username='testuser'"
        assert str(exception) == "Duplicate User with username='testuser'"
    
    def test_duplicate_resource_error_with_field_only(self):
        """フィールドのみの重複エラー初期化テスト（値なし）"""
        # リソースタイプとフィールドだけで例外を作成
        resource_type = "User"
        field = "username"
        exception = DuplicateResourceError(
            resource_type=resource_type,
            field=field
        )
        
        # プロパティと生成されたメッセージの確認
        assert exception.resource_type == resource_type
        assert exception.field == field
        assert exception.value is None
        assert exception.message == "Duplicate User"
        assert str(exception) == "Duplicate User"
    
    def test_duplicate_resource_error_with_custom_message(self):
        """カスタムメッセージでの重複エラー初期化テスト"""
        # すべてのパラメータで例外を作成
        resource_type = "User"
        field = "username"
        value = "testuser"
        custom_message = "Custom duplicate resource message"
        exception = DuplicateResourceError(
            resource_type=resource_type,
            field=field,
            value=value,
            message=custom_message
        )
        
        # プロパティと指定したカスタムメッセージの確認
        assert exception.resource_type == resource_type
        assert exception.field == field
        assert exception.value == value
        assert exception.message == custom_message
        assert str(exception) == custom_message
