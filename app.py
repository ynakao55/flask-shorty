import os
import re
import string
import secrets
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from dotenv import load_dotenv
import validators

# Load .env in local dev
load_dotenv()

def normalize_database_url(url: str) -> str:
    # Render では postgres:// のことがあるので postgresql:// に置き換え
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", ""))

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
app.config["APP_BASE_URL"] = os.getenv("APP_BASE_URL", "")

db = SQLAlchemy(app)

class Link(db.Model):
    __tablename__ = "links"
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False)
    short_code = db.Column(db.String(16), unique=True, index=True, nullable=False)
    clicks = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Link {self.short_code} -> {self.original_url}>"

SAFE_CHARS = string.ascii_letters + string.digits

def generate_code(length: int = 6) -> str:
    return "".join(secrets.choice(SAFE_CHARS) for _ in range(length))

def ensure_schema():
    # 初回アクセス時にテーブル作成
    with app.app_context():
        db.create_all()

@app.before_request
def before_request():
    # 軽量なので毎回でもOK（起動直後にテーブルが無い場合に備える）
    ensure_schema()

@app.get("/health")
def health():
    return {"ok": True}, 200

@app.get("/")
def index():
    recent = Link.query.order_by(Link.id.desc()).limit(5).all()
    return render_template("index.html", recent=recent, title="Flask Shorty")

@app.post("/shorten")
def shorten():
    url = request.form.get("url", "").strip()
    if not url:
        flash("URL を入力してください。", "warning")
        return redirect(url_for("index"))

    # スキーム補完（例：example.com -> http://example.com）
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "http://" + url

    if not validators.url(url):
        flash("URL の形式が正しくありません。", "danger")
        return redirect(url_for("index"))

    # 既に登録済みならそれを返す
    existing = Link.query.filter_by(original_url=url).first()
    if existing:
        short_url = build_short_url(existing.short_code)
        return render_template("result.html", short_url=short_url, link=existing, title="Shortened")

    # 新規作成（短縮コードの衝突回避）
    for _ in range(5):
        code = generate_code(6)
        if not Link.query.filter_by(short_code=code).first():
            break
    else:
        code = generate_code(8)

    link = Link(original_url=url, short_code=code)
    db.session.add(link)
    db.session.commit()

    short_url = build_short_url(code)
    return render_template("result.html", short_url=short_url, link=link, title="Shortened")

def build_short_url(code: str) -> str:
    # Render などで外部URLを固定したい場合は APP_BASE_URL を使用
    base = app.config.get("APP_BASE_URL")
    if base:
        return f"{base.rstrip('/')}/{code}"
    # リクエストから自動生成（http(s)://host/...）
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    host = request.headers.get("Host", request.host)
    return f"{scheme}://{host}/{code}"

@app.get("/<string:short_code>")
def resolve(short_code: str):
    link = Link.query.filter_by(short_code=short_code).first()
    if not link:
        return render_template("404.html"), 404

    # クリック数カウント
    Link.query.filter_by(id=link.id).update({Link.clicks: Link.clicks + 1})
    db.session.commit()
    return redirect(link.original_url, code=302)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    # ローカル実行用
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))