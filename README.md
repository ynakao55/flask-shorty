# Flask Shorty — URL Shortener (Render + PostgreSQL)

シンプルな URL 短縮サービス。Flask + SQLAlchemy + PostgreSQL。  
Render.com にそのままデプロイできます。

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

## ローカル実行

1. 依存をインストール
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. `.env` を作成（`.env.example` をコピー＆修正）
   ```bash
   cp .env.example .env
   # DATABASE_URL を postgresql://... に設定
   ```

3. DB を用意（例：Docker）
   ```bash
   docker run -d --name shorty-db -e POSTGRES_PASSWORD=password -e POSTGRES_DB=shorty -p 5432:5432 postgres:16
   ```

4. 起動
   ```bash
   flask --app app run --debug
   # http://localhost:5000
   ```

## Render へのデプロイ手順

1. GitHub にこのリポジトリを push。
2. Render ダッシュボードで **PostgreSQL** を作成（Free可）。
3. Render で **Web Service** を「Create」 → このリポジトリを選択。
4. 環境変数を設定：
   - `DATABASE_URL`（Render の PG に付与されるURL。`postgres://` の場合は自動で `postgresql://` に置換されます）
   - `SECRET_KEY`（`python -c "import secrets; print(secrets.token_urlsafe(32))"` などで作成）
   - （任意）`APP_BASE_URL`（例：`https://<your-service>.onrender.com`）
5. **Build/Start コマンド**：
   - Build: なし（デフォルト）
   - Start: `Procfile` が自動検出され、`web: gunicorn app:app` で起動
6. 初回アクセス時にテーブルが自動作成されます（`create_all()`）。

## 開発メモ
- Render の `postgres://` 形式は SQLAlchemy では `postgresql://` に変換して使用。
- 例外時は 500 ページにフォールバック。

---

MIT License