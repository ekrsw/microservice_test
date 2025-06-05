# ナレッジメンテナンスサイト - データベース設計

## システム概要

- **目的**: Dynamics365ナレッジベースの修正案・削除案の提出・承認管理
- **利用者**: 約100名
- **主機能**: 提案管理、承認ワークフロー、個人目標管理用集計

## テーブル設計

### 1. Usersテーブル（ユーザー管理）

| カラム名 | データ型 | 制約 | 説明 |
|----------|----------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | ユーザーID |
| username | VARCHAR(50) | NOT NULL, UNIQUE | ログイン用ユーザー名 |
| email | VARCHAR(255) | NOT NULL, UNIQUE | メールアドレス |
| hashed_password | VARCHAR(255) | NOT NULL | ハッシュ化されたパスワード |
| role | VARCHAR(20) CHECK (role IN ('一般ユーザー', 'SV', '管理者')) | NOT NULL | ユーザー権限 |
| group_id | UUID | FK | 承認グループID |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

### 2. Groupsテーブル（承認グループ管理）

| カラム名 | データ型 | 制約 | 説明 |
|----------|----------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | グループID |
| name | VARCHAR(100) | NOT NULL | グループ名 |
| description | TEXT | NULL | グループ説明 |

### 3. InfoCategoriesテーブル（情報カテゴリ管理）

| カラム名 | データ型 | 制約 | 説明 |
|----------|----------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | カテゴリID |
| name | VARCHAR(100) | NOT NULL | カテゴリ名 |
| description | TEXT | NULL | カテゴリ説明 |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

### 4. Articlesテーブル（記事マスタ管理）

| カラム名 | データ型 | 制約 | 説明 |
|----------|----------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | ID |
| article_id | VARCHAR(50) | NOT NULL, UNIQUE | Dynamics365記事番号 |
| article | VARCHAR(255) | NOT NULL, UNIQUE | Dynamics365記事PK（カスタムUUID形式） |
| approval_group_id | UUID | FK, NOT NULL | 承認対象グループID |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

### 5. Proposalsテーブル（提案管理）

| カラム名 | データ型 | 制約 | 説明 |
|----------|----------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 提案ID |
| user_id | UUID | FK, NOT NULL | 提案者ID |
| article_id | VARCHAR(50) | NOT NULL | Dynamics365記事番号（Articlesテーブルと連携） |
| article | VARCHAR(255) | NOT NULL | Dynamics365記事PK（Articlesテーブルと連携） |
| type | VARCHAR(10) CHECK (type IN ('修正', '削除')) | NOT NULL | 提案タイプ |
| status | VARCHAR(10) CHECK (status IN ('申請中', '承認済み', '却下')) | NOT NULL DEFAULT '申請中' | 承認状況 |
| title | VARCHAR(500) | NOT NULL | 記事タイトル |
| info_category_id | UUID | FK | 情報カテゴリID |
| keywords | TEXT | NULL | キーワード |
| importance | BOOLEAN | NULL | 重要度フラグ |
| published_start | DATE | NULL | 公開開始日 |
| published_end | DATE | NULL | 公開終了日 |
| target | VARCHAR(10) CHECK (target IN ('社内向け', '社外向け', '該当なし')) | NULL | 対象 |
| question | TEXT | NULL | 質問内容 |
| answer | TEXT | NULL | 回答内容 |
| add_comments | TEXT | NULL | 追加コメント |
| reason | TEXT | NOT NULL | 提案理由 |
| approval_group_id | UUID | FK, NOT NULL | 承認対象グループID（Articlesテーブルから自動取得） |
| approved_by | UUID | FK, NULL | 承認者ID |
| approved_at | TIMESTAMPTZ | NULL | 承認日時 |
| rejection_reason | TEXT | NULL | 却下理由 |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

### 6. ProposalsBeforeテーブル（修正前データ管理）

| カラム名 | データ型 | 制約 | 説明 |
|----------|----------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | ID |
| proposal_id | UUID | FK, NOT NULL | 提案ID |
| title_before | VARCHAR(500) | NULL | 修正前タイトル |
| info_category_id_before | UUID | FK, NULL | 修正前カテゴリID |
| keywords_before | TEXT | NULL | 修正前キーワード |
| importance_before | BOOLEAN | NULL | 修正前重要度フラグ |
| published_start_before | DATE | NULL | 修正前公開開始日 |
| published_end_before | DATE | NULL | 修正前公開終了日 |
| target_before | VARCHAR(10) CHECK (target_before IN ('社内向け', '社外向け', '該当なし')) | NULL | 修正前対象 |
| question_before | TEXT | NULL | 修正前質問内容 |
| answer_before | TEXT | NULL | 修正前回答内容 |
| add_comments_before | TEXT | NULL | 修正前追加コメント |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP | 作成日時 |

## リレーション設計

### 外部キー制約

- `Users.group_id` → `Groups.id`
- `Articles.approval_group_id` → `Groups.id`
- `Proposals.user_id` → `Users.id`
- `Proposals.article_id` → `Articles.article_id` （参照整合性）
- `Proposals.info_category_id` → `InfoCategories.id`
- `Proposals.approval_group_id` → `Groups.id` （Articlesテーブルから自動取得）
- `Proposals.approved_by` → `Users.id`
- `ProposalsBefore.proposal_id` → `Proposals.id`
- `ProposalsBefore.info_category_id_before` → `InfoCategories.id`

### ER図（概念図）

```
Groups ←→ Users
  ↓
Articles
  ↓
Proposals ←→ ProposalsBefore
  ↓
InfoCategories
```

## データ運用フロー

### 提案作成時の処理フロー

1. **記事選択**
   - ユーザーがDynamics365記事を検索・選択
   - `Articles`テーブルから`approval_group_id`を自動取得

2. **データ保存（修正案の場合）**
   - Dynamics365から現在の記事データを取得
   - `ProposalsBefore`テーブルに修正前データを保存
   - `Proposals`テーブルに修正後データを保存
   - `approval_group_id`を自動設定

3. **データ保存（削除案の場合）**
   - Dynamics365から現在の記事データを取得
   - `ProposalsBefore`テーブルに削除対象データを保存
   - `Proposals`テーブルには参考情報として現在データを保存

### 承認処理フロー

1. **承認待ち表示**
   - SVが担当グループ（`Users.group_id` = `Articles.approval_group_id`）の提案を表示

2. **修正前後比較**
   - `ProposalsBefore`と`Proposals`をJOINして差分表示

3. **承認・却下処理**
   - `Proposals.status`を更新
   - `Proposals.approved_by`に承認者IDを設定
   - `Proposals.approved_at`に承認日時を設定
   - 却下の場合は`Proposals.rejection_reason`に理由を記録

### 集計処理

1. **個人統計**
   ```sql
   -- 月次提案数
   SELECT COUNT(*) FROM Proposals 
   WHERE user_id = $1 AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', $2::date);
   
   -- 承認率
   SELECT 
     COUNT(*) as total,
     SUM(CASE WHEN status = '承認済み' THEN 1 ELSE 0 END) as approved
   FROM Proposals 
   WHERE user_id = $1;
   ```

2. **全体統計**
   ```sql
   -- グループ別集計
   SELECT g.name, COUNT(p.id) as proposal_count
   FROM Groups g
   LEFT JOIN Proposals p ON g.id = p.approval_group_id
   GROUP BY g.id, g.name;
   ```

## インデックス設計

### 主要インデックス

```sql
-- Proposals テーブル
CREATE INDEX idx_proposals_user_id ON Proposals(user_id);
CREATE INDEX idx_proposals_article_id ON Proposals(article_id);
CREATE INDEX idx_proposals_status ON Proposals(status);
CREATE INDEX idx_proposals_approval_group ON Proposals(approval_group_id);
CREATE INDEX idx_proposals_created_at ON Proposals(created_at);

-- Users テーブル
CREATE INDEX idx_users_group_id ON Users(group_id);
CREATE INDEX idx_users_role ON Users(role);

-- Articles テーブル
CREATE INDEX idx_articles_approval_group ON Articles(approval_group_id);

-- ProposalsBefore テーブル
CREATE INDEX idx_proposals_before_proposal_id ON ProposalsBefore(proposal_id);
```

## データ整合性

### 制約事項

1. **必須データ**
   - 提案理由（`Proposals.reason`）は必須
   - 承認グループID（`Proposals.approval_group_id`）は必須
   - 却下時の却下理由（`Proposals.rejection_reason`）は必須

2. **ステータス遷移**
   - 申請中 → 承認済み または 却下
   - 承認済み・却下からの変更は不可（管理者権限除く）

3. **承認権限**
   - SVは自分が所属するグループの提案のみ承認可能
   - 自分の提案は承認不可

### トリガー・制約

```sql
-- 承認日時の自動設定（PostgreSQL関数版）
CREATE OR REPLACE FUNCTION update_approved_at()
RETURNS TRIGGER AS $
BEGIN
  IF NEW.status = '承認済み' AND OLD.status = '申請中' THEN
    NEW.approved_at = NOW();
  END IF;
  RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER tr_proposals_approved_at 
  BEFORE UPDATE ON Proposals
  FOR EACH ROW
  EXECUTE FUNCTION update_approved_at();

-- updated_at自動更新関数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- updated_atトリガー
CREATE TRIGGER tr_users_updated_at
  BEFORE UPDATE ON Users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_infocategories_updated_at
  BEFORE UPDATE ON InfoCategories
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_articles_updated_at
  BEFORE UPDATE ON Articles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER tr_proposals_updated_at
  BEFORE UPDATE ON Proposals
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- 却下理由の必須チェック
ALTER TABLE Proposals 
ADD CONSTRAINT chk_rejection_reason 
CHECK (
  (status != '却下') OR 
  (status = '却下' AND rejection_reason IS NOT NULL AND rejection_reason != '')
);
```

## 初期データ

### マスタデータ例

```sql
-- UUID拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 承認グループ
INSERT INTO Groups (id, name, description) VALUES
(gen_random_uuid(), 'Aグループ', 'IT関連記事の承認'),
(gen_random_uuid(), 'Bグループ', '業務関連記事の承認'),
(gen_random_uuid(), 'Cグループ', '人事・総務関連記事の承認');

-- 情報カテゴリ
INSERT INTO InfoCategories (id, name, description) VALUES
(gen_random_uuid(), 'IT', 'システム・技術関連'),
(gen_random_uuid(), '業務', '業務プロセス・手順'),
(gen_random_uuid(), '人事', '人事制度・福利厚生'),
(gen_random_uuid(), '総務', '総務・庶務関連');

-- 管理者ユーザー
INSERT INTO Users (id, username, email, hashed_password, role, group_id) VALUES
(gen_random_uuid(), 'admin', 'admin@company.com', '$hashed_password', '管理者', 
 (SELECT id FROM Groups WHERE name = 'Aグループ' LIMIT 1));
```

## バックアップ・保守

### バックアップ戦略

- **日次**: 差分バックアップ
- **週次**: 完全バックアップ
- **保持期間**: 3ヶ月

### 定期メンテナンス

- **インデックス再構築**: 月次
- **統計情報更新**: 週次
- **不要データ削除**: 年次（ログデータのみ）
