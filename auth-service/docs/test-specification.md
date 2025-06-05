# Auth Service テスト仕様書

## 概要

Auth Serviceのテスト仕様書です。単体テスト（Unit Test）を中心とした包括的なテスト戦略とテストケースを定義しています。

## テスト戦略

### テストレベル
- **単体テスト（Unit Test）**: 個別のコンポーネント、関数、クラスのテスト
- **統合テスト（Integration Test）**: 複数のコンポーネント間の連携テスト
- **APIテスト**: エンドポイントの動作テスト

### テストフレームワーク
- **pytest**: メインのテストフレームワーク
- **pytest-asyncio**: 非同期テストのサポート
- **unittest.mock**: モックオブジェクトの作成
- **FastAPI TestClient**: APIエンドポイントのテスト

### テストデータベース
- **SQLite（インメモリ）**: テスト専用の軽量データベース
- **各テスト関数ごとに独立したデータベースセッション**

## テスト環境設定

### conftest.py
テスト全体で共有されるフィクスチャとセットアップを定義

#### 主要フィクスチャ

| フィクスチャ名 | スコープ | 説明 |
|---------------|---------|------|
| `db_engine` | function | インメモリSQLiteエンジン |
| `db_session` | function | データベースセッション |
| `unique_username` | function | ユニークなユーザー名生成 |
| `unique_email` | function | ユニークなメールアドレス生成 |
| `unique_password` | function | ユニークなパスワード生成（1-16文字、半角英数字） |
| `unique_user_id` | function | ユニークなユーザーID（UUID）生成 |
| `test_user` | function | テスト用ユーザーの作成 |

#### データベース設定
```python
# インメモリSQLiteデータベース
engine = create_async_engine("sqlite+aiosqlite:///:memory:")

# 各テスト後にロールバック
async with AsyncSessionLocal() as session:
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
```

## テストカテゴリ別仕様

### 1. APIエンドポイントテスト

**ファイル**: `tests/unit/api/test_api_endpoints.py`

#### 1.1 ユーザー登録エンドポイント

**テストケース**: `test_register_endpoint`
- **目的**: ユーザー登録が正常に動作することを確認
- **モック対象**: 
  - `auth_user_crud.create`
  - `publish_user_created`
- **検証項目**:
  - HTTPステータス: 202 Accepted
  - レスポンスにusername, emailが含まれる
  - レスポンスにpasswordが含まれない
  - RabbitMQメッセージが発行される

**テストケース**: `test_register_endpoint_validation_error`
- **目的**: バリデーションエラーの処理を確認
- **検証項目**:
  - HTTPステータス: 422 Unprocessable Entity
  - エラー詳細が含まれる

#### 1.2 ログインエンドポイント

**テストケース**: `test_login_endpoint`
- **目的**: ログインが正常に動作することを確認
- **モック対象**:
  - `auth_user_crud.get_by_username`
  - `verify_password`
  - `create_access_token`
  - `create_refresh_token`
- **検証項目**:
  - HTTPステータス: 200 OK
  - アクセストークンとリフレッシュトークンが返される
  - token_typeが"bearer"

**テストケース**: `test_login_endpoint_authentication_failure`
- **目的**: 認証失敗時の処理を確認
- **検証項目**:
  - HTTPステータス: 401 Unauthorized
  - 適切なエラーメッセージ

#### 1.3 トークンリフレッシュエンドポイント

**テストケース**: `test_refresh_token_endpoint`
- **目的**: トークン更新が正常に動作することを確認
- **モック対象**:
  - `verify_refresh_token`
  - `create_access_token`
  - `create_refresh_token`
  - `blacklist_token`
  - `revoke_refresh_token`
  - `auth_user_crud.get_by_id`

**テストケース**: `test_refresh_token_endpoint_invalid_token`
- **目的**: 無効なリフレッシュトークンの処理を確認
- **検証項目**:
  - HTTPステータス: 401 Unauthorized

#### 1.4 ユーザー情報取得エンドポイント

**テストケース**: `test_me_endpoint`
- **目的**: 認証済みユーザー情報取得を確認
- **モック対象**: `get_current_user`依存関係
- **検証項目**:
  - HTTPステータス: 200 OK
  - ユーザー情報が正しく返される

#### 1.5 ログアウトエンドポイント

**テストケース**: `test_logout_endpoint`
- **目的**: ログアウト処理を確認
- **モック対象**:
  - `blacklist_token`
  - `revoke_refresh_token`
- **検証項目**:
  - HTTPステータス: 200 OK
  - 適切な成功メッセージ

---

### 2. CRUD操作テスト

**ファイル**: `tests/unit/crud/test_crud_auth_user_normal.py`

#### 2.1 ユーザー作成テスト

**テストケース**: `test_create_auth_user`
- **目的**: ユーザーの作成機能を確認
- **検証項目**:
  - ユーザーが正しく作成される
  - パスワードがハッシュ化される
  - パスワード検証が正常に動作する
  - データベースに正しく保存される

**テストケース**: `test_create_multiple_auth_users`
- **目的**: 複数ユーザーの一括作成を確認
- **検証項目**:
  - 指定した数のユーザーが作成される
  - 各ユーザーが正しく保存される
  - 一意制約が正しく動作する

#### 2.2 ユーザー取得テスト

**テストケース**: `test_get_auth_user_by_email`
- **目的**: メールアドレスによるユーザー取得を確認
- **検証項目**:
  - 正しいユーザーが取得される
  - 存在しないメールアドレスでUserNotFoundErrorが発生

**テストケース**: `test_get_all_auth_users`
- **目的**: 全ユーザー取得機能を確認
- **検証項目**:
  - 作成したユーザーがすべて取得される
  - ユーザー数が正しい

**テストケース**: `test_get_auth_user_by_nonexistent_*`
- **目的**: 存在しないリソースへのアクセス処理を確認
- **検証項目**:
  - UserNotFoundErrorが正しく発生する

#### 2.3 ユーザー更新テスト

**テストケース**: `test_update_auth_user_username`
- **目的**: ユーザー名更新機能を確認
- **検証項目**:
  - ユーザー名が正しく更新される
  - 他のフィールドは変更されない
  - データベースに正しく反映される

**テストケース**: `test_update_auth_user_email`
- **目的**: メールアドレス更新機能を確認

**テストケース**: `test_update_auth_user_password`
- **目的**: パスワード更新機能を確認
- **検証項目**:
  - 現在のパスワード検証が正しく動作する
  - 新しいパスワードがハッシュ化される
  - 誤った現在のパスワードでエラーが発生する

#### 2.4 ユーザー削除テスト

**テストケース**: `test_delete_auth_user_by_username`
- **目的**: ユーザー削除機能を確認
- **検証項目**:
  - ユーザーが正しく削除される
  - 削除後に取得できなくなる

---

### 3. セキュリティ機能テスト

**ファイル**: `tests/unit/security/test_security.py`

#### 3.1 パスワード関連テスト

**テストケース**: `test_password_hash`
- **目的**: パスワードハッシュ化機能を確認
- **検証項目**:
  - ハッシュ値が元のパスワードと異なる
  - 同じパスワードでも異なるハッシュ値が生成される

**テストケース**: `test_verify_password`
- **目的**: パスワード検証機能を確認
- **検証項目**:
  - 正しいパスワードで検証成功
  - 誤ったパスワードで検証失敗

#### 3.2 アクセストークン関連テスト

**テストケース**: `test_create_access_token`
- **目的**: アクセストークン生成機能を確認
- **検証項目**:
  - トークンが文字列として生成される
  - ペイロードに必要な情報が含まれる
  - カスタム有効期限が正しく設定される

**テストケース**: `test_verify_token`
- **目的**: トークン検証機能を確認
- **検証項目**:
  - 有効なトークンで検証成功
  - 無効なトークンで検証失敗
  - ブラックリストチェックが動作する

#### 3.3 トークンブラックリスト関連テスト

**テストケース**: `test_blacklist_token`
- **目的**: トークンブラックリスト登録機能を確認
- **モック対象**: Redis操作
- **検証項目**:
  - Redisに正しくトークンが保存される
  - 無効なトークンで失敗する
  - 例外発生時に適切に処理される

**テストケース**: `test_is_token_blacklisted`
- **目的**: ブラックリストチェック機能を確認
- **検証項目**:
  - ブラックリストに登録されたトークンでTrue
  - 未登録のトークンでFalse
  - 機能無効時は常にFalse

#### 3.4 リフレッシュトークン関連テスト

**テストケース**: `test_create_refresh_token`
- **目的**: リフレッシュトークン生成機能を確認
- **モック対象**: Redis操作
- **検証項目**:
  - トークンが生成される
  - Redisに正しく保存される
  - 有効期限が正しく設定される

**テストケース**: `test_verify_refresh_token`
- **目的**: リフレッシュトークン検証機能を確認
- **検証項目**:
  - 有効なトークンでユーザーIDが返される
  - 無効なトークンでNoneが返される
  - 有効期限切れでJWTErrorが発生する

**テストケース**: `test_revoke_refresh_token`
- **目的**: リフレッシュトークン無効化機能を確認
- **検証項目**:
  - 正常に削除された場合True
  - 存在しないトークンでFalse

---

### 4. その他のコンポーネントテスト

#### 4.1 設定テスト
**ファイル**: `tests/unit/core/test_config.py`
- 設定値の読み込みと検証

#### 4.2 例外処理テスト
**ファイル**: `tests/unit/core/test_exceptions.py`
- カスタム例外の動作確認

#### 4.3 ログ機能テスト
**ファイル**: `tests/unit/core/test_logging.py`
- ログ出力機能の確認

#### 4.4 Redis機能テスト
**ファイル**: `tests/unit/core/test_redis.py`
- Redis接続と操作の確認

#### 4.5 データベース初期化テスト
**ファイル**: `tests/unit/db/test_init.py`
- データベース初期化処理の確認

#### 4.6 スキーマ検証テスト
**ファイル**: `tests/unit/schemas/test_auth_user.py`
- Pydanticスキーマのバリデーション確認

#### 4.7 メッセージング機能テスト
**ファイル**: `tests/unit/messaging/test_messaging.py`
- RabbitMQメッセージング機能の確認

---

## テスト実行

### 基本的なテスト実行
```bash
# すべてのテストを実行
pytest

# 特定のディレクトリのテストを実行
pytest tests/unit/api/

# 特定のファイルのテストを実行
pytest tests/unit/api/test_api_endpoints.py

# 特定のテストケースを実行
pytest tests/unit/api/test_api_endpoints.py::test_register_endpoint

# 詳細な出力で実行
pytest -v

# カバレッジレポート付きで実行
pytest --cov=app --cov-report=html
```

### 非同期テストの実行
```bash
# 非同期テストのみ実行
pytest -m asyncio

# 非同期テストを詳細出力で実行
pytest -v -m asyncio
```

---

## モック戦略

### 外部依存関係のモック

#### データベース
- インメモリSQLiteを使用
- 各テスト関数で独立したセッション

#### Redis
- `unittest.mock.AsyncMock`を使用
- Redis操作をモック化

#### RabbitMQ
- メッセージ発行機能をモック化
- 非同期処理の結果をモック

#### JWT署名
- テスト用の公開鍵/秘密鍵を使用

### モックの原則
1. **外部サービス**: 常にモック化
2. **データベース**: テスト専用インスタンス使用
3. **時間依存処理**: 固定値でモック化
4. **ランダム値**: 予測可能な値でモック化

---

## テストデータ管理

### テストデータの原則
1. **一意性**: 各テストで一意なデータを使用
2. **独立性**: テスト間でデータが干渉しない
3. **クリーンアップ**: テスト後にデータを削除
4. **リアリスティック**: 実際のデータに近い形式

### データ生成戦略
```python
# ユニークなユーザー名（半角英数字のみ）
username = f"user{uuid.uuid4().hex[:10]}"

# ユニークなメールアドレス
email = f"user_{uuid.uuid4()}@example.com"

# ランダムなパスワード（1-16文字、半角英数字のみ）
password = ''.join(random.choice(string.ascii_letters + string.digits) 
                  for _ in range(random.randint(1, 16)))
```

---

## テストカバレッジ目標

### カバレッジ目標
- **全体**: 90%以上
- **API層**: 95%以上
- **CRUD層**: 95%以上
- **セキュリティ層**: 95%以上
- **コア機能**: 90%以上

### カバレッジ除外項目
- 設定ファイル
- マイグレーションファイル
- 外部ライブラリのラッパー
- デバッグ用コード

---

## 継続的インテグレーション

### CI/CDパイプライン
1. **コードチェック**: flake8, black, isort
2. **型チェック**: mypy
3. **セキュリティチェック**: bandit
4. **テスト実行**: pytest
5. **カバレッジレポート**: codecov

### テスト環境
- **Python**: 3.11+
- **データベース**: SQLite（テスト）、PostgreSQL（本番）
- **Redis**: Redis（モック）
- **RabbitMQ**: RabbitMQ（モック）

---

## トラブルシューティング

### よくある問題

#### 1. 非同期テストの失敗
```python
# 解決方法: @pytest.mark.asyncioデコレータを追加
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

#### 2. データベースセッションエラー
```python
# 解決方法: セッションの適切なクリーンアップ
async with AsyncSessionLocal() as session:
    try:
        # テスト処理
        yield session
    finally:
        await session.rollback()
        await session.close()
```

#### 3. モックの設定ミス
```python
# 解決方法: パッチパスの確認
# ❌ 間違い
@patch("redis.from_url")

# ✅ 正しい
@patch("app.core.security.redis.asyncio.from_url")
```

#### 4. 一意制約違反
```python
# 解決方法: ユニークなテストデータの生成
username = f"testuser_{uuid.uuid4().hex[:8]}"
email = f"test_{uuid.uuid4()}@example.com"
```

---

## テスト品質向上のガイドライン

### テストコードの品質
1. **可読性**: テストの目的が明確
2. **保守性**: 変更に強い構造
3. **信頼性**: 安定した結果
4. **効率性**: 高速な実行

### ベストプラクティス
1. **AAA パターン**: Arrange, Act, Assert
2. **単一責任**: 1つのテストで1つの機能
3. **独立性**: テスト間の依存関係を排除
4. **明確な命名**: テストの目的が分かる名前

### テストレビューチェックリスト
- [ ] テストの目的が明確か
- [ ] 適切なモックが使用されているか
- [ ] エラーケースがテストされているか
- [ ] テストデータがクリーンアップされているか
- [ ] 非同期処理が正しく処理されているか
