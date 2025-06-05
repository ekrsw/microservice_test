# Auth Service テーブル設計

## 概要

Auth Serviceは認証機能を提供するマイクロサービスです。ユーザーの認証情報を管理し、JWT トークンベースの認証を実装しています。

## テーブル一覧

### auth_users テーブル

ユーザーの認証情報を格納するメインテーブルです。

#### テーブル構造

| カラム名 | データ型 | NULL許可 | デフォルト値 | 制約 | 説明 |
|---------|---------|---------|------------|-----|-----|
| id | UUID | NOT NULL | uuid.uuid4() | PRIMARY KEY, INDEX | レコードの一意識別子 |
| username | String | NOT NULL | - | UNIQUE, INDEX | ユーザー名（ログイン用） |
| email | String | NOT NULL | - | UNIQUE, INDEX | メールアドレス（ログイン用） |
| hashed_password | String | NOT NULL | - | - | ハッシュ化されたパスワード |
| user_id | UUID | NULL | - | UNIQUE, INDEX | 他のサービスとの連携用ユーザーID |
| created_at | DateTime(timezone=True) | NOT NULL | 現在時刻 | - | レコード作成日時 |
| updated_at | DateTime(timezone=True) | NOT NULL | 現在時刻 | ON UPDATE | レコード更新日時 |

#### インデックス

- `ix_auth_users_id`: id カラムのインデックス
- `ix_auth_users_username`: username カラムの一意インデックス
- `ix_auth_users_email`: email カラムの一意インデックス
- `ix_auth_users_user_id`: user_id カラムの一意インデックス

#### 制約

- **PRIMARY KEY**: `id`
- **UNIQUE制約**: 
  - `username`: 同じユーザー名の重複を防ぐ
  - `email`: 同じメールアドレスの重複を防ぐ
  - `user_id`: 他サービス連携時の重複を防ぐ

## データベース設計の特徴

### 1. 基底クラス（Base）の共通フィールド

すべてのテーブルは `Base` クラスを継承し、以下の共通フィールドを持ちます：

- `id`: UUID型の主キー（自動生成）
- `created_at`: レコード作成日時（タイムゾーン対応）
- `updated_at`: レコード更新日時（自動更新）

### 2. セキュリティ考慮事項

- **パスワードハッシュ化**: 平文パスワードは保存せず、ハッシュ化されたパスワードのみを保存
- **一意制約**: username と email に一意制約を設定し、重複アカウントを防止
- **インデックス**: ログイン時の検索性能を向上させるため、username と email にインデックスを設定

### 3. マイクロサービス連携

- `user_id`: 他のマイクロサービス（user-service等）との連携用フィールド
- 認証サービス独自のIDと、システム全体で使用するuser_idを分離

## マイグレーション情報

- **初回マイグレーション**: `51bcfb6e6872_create_tables.py`
- **作成日**: 2025-04-30 23:19:59
- **Alembic**: データベーススキーマのバージョン管理に使用

## 使用技術

- **ORM**: SQLAlchemy 2.0
- **マイグレーション**: Alembic
- **データベース**: PostgreSQL（推奨）
- **UUID生成**: Python標準ライブラリのuuid.uuid4()

## 今後の拡張予定

将来的に以下の機能追加が検討される場合のテーブル設計案：

### 1. ロール・権限管理
```sql
-- roles テーブル
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- user_roles テーブル（多対多の関連）
CREATE TABLE user_roles (
    user_id UUID REFERENCES auth_users(id),
    role_id UUID REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
```

### 2. セッション管理
```sql
-- sessions テーブル
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth_users(id),
    token_hash VARCHAR NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### 3. ログイン履歴
```sql
-- login_history テーブル
CREATE TABLE login_history (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth_users(id),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE
);
