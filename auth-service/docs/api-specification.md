# Auth Service API仕様書

## 概要

Auth Serviceは認証機能を提供するマイクロサービスです。JWT トークンベースの認証システムを実装し、ユーザー登録、ログイン、トークン管理機能を提供します。

## ベース情報

- **ベースURL**: `http://localhost:8080`
- **APIバージョン**: v1
- **APIプレフィックス**: `/api/v1`
- **認証方式**: Bearer Token (JWT)

## 共通レスポンスヘッダー

すべてのAPIレスポンスには以下のヘッダーが含まれます：

- `X-Request-ID`: リクエストの一意識別子
- `X-Process-Time`: 処理時間（秒）

## エンドポイント一覧

### 1. ユーザー登録

**POST** `/api/v1/auth/register`

ユーザーの新規登録を行います。非同期処理でuser-serviceと連携します。

#### リクエスト

```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string"
}
```

#### バリデーション

- `username`: 3-50文字、半角英数字とアンダースコア(_)のみ
- `email`: 有効なメールアドレス形式
- `password`: 1-16文字、半角英数字のみ

#### レスポンス

**成功時 (202 Accepted)**
```json
{
  "message": "ユーザー登録リクエストを受け付けました",
  "username": "string",
  "email": "user@example.com"
}
```

**エラー時 (422 Unprocessable Entity)**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "username"],
      "msg": "String should have at least 3 characters",
      "input": "ab"
    }
  ]
}
```

**エラー時 (500 Internal Server Error)**
```json
{
  "detail": "ユーザー登録リクエストの処理中にエラーが発生しました"
}
```

---

### 2. ログイン

**POST** `/api/v1/auth/login`

ユーザー認証を行い、アクセストークンとリフレッシュトークンを発行します。

#### リクエスト

Form Data形式（OAuth2PasswordRequestForm）:
- `username`: ユーザー名
- `password`: パスワード

#### レスポンス

**成功時 (200 OK)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**エラー時 (401 Unauthorized)**
```json
{
  "detail": "ユーザー名またはパスワードが正しくありません"
}
```

---

### 3. ログアウト

**POST** `/api/v1/auth/logout`

アクセストークンとリフレッシュトークンを無効化します。

#### リクエスト

```json
{
  "access_token": "string",
  "refresh_token": "string"
}
```

#### レスポンス

**成功時 (200 OK)**
```json
{
  "detail": "ログアウトしました"
}
```

**エラー時 (400 Bad Request)**
```json
{
  "detail": "リフレッシュトークンの無効化に失敗しました。ログアウトできません。"
}
```

---

### 4. トークン更新

**POST** `/api/v1/auth/refresh`

リフレッシュトークンを使用して新しいアクセストークンを発行します。

#### リクエスト

```json
{
  "access_token": "string",
  "refresh_token": "string"
}
```

#### レスポンス

**成功時 (200 OK)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**エラー時 (401 Unauthorized)**
```json
{
  "detail": "無効なリフレッシュトークンです"
}
```

---

### 5. 現在のユーザー情報取得

**GET** `/api/v1/auth/me`

認証済みユーザーの情報を取得します。

#### 認証

Bearer Token（アクセストークン）が必要

#### レスポンス

**成功時 (200 OK)**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "string",
  "email": "user@example.com",
  "user_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**エラー時 (401 Unauthorized)**
```json
{
  "detail": "認証が必要です"
}
```

---

### 6. パスワード変更

**POST** `/api/v1/auth/password/change`

認証済みユーザーのパスワードを変更します。

#### 認証

Bearer Token（アクセストークン）が必要

#### リクエスト

```json
{
  "current_password": "string",
  "new_password": "string"
}
```

#### バリデーション

- `new_password`: 1-16文字、半角英数字のみ

#### レスポンス

**成功時 (200 OK)**
```json
{
  "detail": "パスワードが正常に変更されました"
}
```

**エラー時 (400 Bad Request)**
```json
{
  "detail": "現在のパスワードが正しくありません"
}
```

---

### 7. ユーザー情報更新（内部API）

**PUT** `/api/v1/auth/update_user/{auth_user_id}`

他のマイクロサービスからユーザー情報を更新するための内部APIです。

#### パスパラメータ

- `auth_user_id`: UUID形式のユーザーID

#### リクエスト

```json
{
  "username": "string",
  "email": "user@example.com",
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### レスポンス

**成功時 (200 OK)**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "string",
  "email": "user@example.com",
  "user_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**エラー時 (404 Not Found)**
```json
{
  "detail": "User not found"
}
```

**エラー時 (400 Bad Request)**
```json
{
  "detail": "Username already exists"
}
```

---

## システムエンドポイント

### ルート

**GET** `/`

サービスの基本情報を返します。

#### レスポンス

```json
{
  "message": "認証サービスAPI",
  "version": "1.0.0",
  "docs_url": "/docs"
}
```

### ヘルスチェック

**GET** `/health`

サービスの稼働状況を確認します。

#### レスポンス

```json
{
  "status": "healthy"
}
```

---

## エラーハンドリング

### HTTPステータスコード

- `200 OK`: 正常処理
- `202 Accepted`: 非同期処理受付
- `400 Bad Request`: リクエストエラー
- `401 Unauthorized`: 認証エラー
- `404 Not Found`: リソースが見つからない
- `422 Unprocessable Entity`: バリデーションエラー
- `500 Internal Server Error`: サーバーエラー

### バリデーションエラー形式

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "field_name"],
      "msg": "エラーメッセージ",
      "input": "入力値"
    }
  ],
  "body": "リクエストボディ"
}
```

---

## 認証・認可

### JWT トークン

- **アクセストークン**: API認証に使用（短期間有効）
- **リフレッシュトークン**: アクセストークン更新に使用（長期間有効）

### トークンペイロード

```json
{
  "sub": "auth_user_id",
  "user_id": "system_user_id",
  "username": "username",
  "exp": 1234567890
}
```

### 認証ヘッダー

```
Authorization: Bearer <access_token>
```

---

## セキュリティ考慮事項

1. **パスワードハッシュ化**: bcryptを使用してパスワードをハッシュ化
2. **トークンブラックリスト**: ログアウト時にトークンを無効化
3. **CORS設定**: 本番環境では適切なオリジン制限を設定
4. **リクエストID**: 全リクエストにユニークIDを付与してトレーサビリティを確保
5. **ログ記録**: 認証関連の操作を詳細にログ記録

---

## マイクロサービス連携

### RabbitMQ メッセージング

- **ユーザー作成イベント**: user-serviceにユーザー作成を依頼
- **ユーザー作成レスポンス**: user-serviceからの作成結果を受信
- **パスワード一時保存**: Redisを使用してパスワードを一時保存

### Redis使用用途

- パスワード一時保存（ユーザー登録時）
- トークンブラックリスト管理
- リフレッシュトークン管理

---

## 開発・テスト

### API ドキュメント

- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`

### ログレベル

- `DEBUG`: 詳細なデバッグ情報
- `INFO`: 一般的な情報（デフォルト）
- `WARNING`: 警告
- `ERROR`: エラー情報

### 環境変数

主要な設定項目：
- `ENVIRONMENT`: 実行環境（development/production）
- `LOG_LEVEL`: ログレベル
- `ACCESS_TOKEN_EXPIRE_MINUTES`: アクセストークン有効期限
- `DATABASE_URL`: データベース接続URL
- `REDIS_URL`: Redis接続URL
- `RABBITMQ_URL`: RabbitMQ接続URL
