# Flask Shorty — URL Shortener (Render + PostgreSQL)

シンプルな URL 短縮サービス。
Flask + SQLAlchemy + PostgreSQL。  

ローカル（Docker）で実行する方法と、公開URLから試す方法を記載します。

## 機能
- URL 短縮（6文字コード）
- 既存URLは再利用（重複作成しない）
- クリック数カウント
- バリデーション（`validators`）
- 404/500 の簡易ページ
- `/health` ヘルスチェック

## 画面
- `/` フォーム（URL入力）
- `/shorten` POSTで短縮作成（結果表示）
- `/<code>` で元URLへリダイレクト


## ローカルで実行する方法（Docker / WSL）

### 前提
以下がインストール・設定済みであることを前提とします。

- WSL（Windows Subsystem for Linux）
- Docker Desktop
- WSL と Docker の連携設定（WSL integration）が有効

---

### 1. Git をインストール（未インストールの場合）

```bash
sudo apt update
sudo apt install -y git
```

---

### 2. リポジトリをクローン

#### Public リポジトリ（HTTPS）
```bash
git clone https://github.com/ynakao55/flask-shorty.git
cd flask-shorty
```

---

### 3. 起動（Docker Compose）

#### 通常の起動 / 停止
```bash
docker compose up -d --build
docker compose down
```

#### 確実に作り直して起動したい場合（推奨）
コンテナ・ボリューム・不要な関連コンテナも整理してから再作成します。

```bash
docker compose down -v --remove-orphans
docker compose up -d --build --force-recreate
```

---

### 4. ブラウザで開く

起動後、以下のURLをブラウザで開いてください。

- http://localhost:8081

---

## 公開URLから試す方法（Web）

以下のURLからアクセスできます。

- https://flask-shorty.ysnko.com

### 初回アクセス時の流れ
1. 上記リンクを開く
2. ログイン方法で **メール（PINコード）** を選択
3. メールアドレスを入力
4. 届いたメールに記載された **PINコード** を確認
5. PINコードを入力してログイン

### なぜPINが必要？
このサイトは Cloudflare Access により保護されており、  
**本人確認のためにワンタイムPIN（使い捨てコード）** を使用しています。  
パスワードを作成・管理しなくても、メールで簡単に本人確認できます。

---

## ローカル実行時の補足（トラブルシュート）

### 起動しているか確認
```bash
docker compose ps
```

### ログを確認
```bash
docker compose logs -f
```

### 画面が開かない / 反映されない場合
```bash
docker compose down -v --remove-orphans
docker compose up -d --build --force-recreate
```
---

## ライセンス

MIT License

---
