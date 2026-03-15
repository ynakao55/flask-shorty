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

load_dotenv()

def build_database_uri() -> str:
    # Render 環境で DATABASE_URL を直接使いたい場合
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    # TiDB 個別パラメータから組み立てる場合
    host = os.getenv("TIDB_HOST", "").strip()
    port = os.getenv("TIDB_PORT", "4000").strip()
    user = os.getenv("TIDB_USER", "").strip()
    password = os.getenv("TIDB_PASSWORD", "").strip()
    db_name = os.getenv("TIDB_DB_NAME", "").strip()

    if host and user and db_name:
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

    # ローカル用フォールバック
    return "sqlite:///local.db"

DATABASE_URL = build_database_uri()
CA_PATH = os.getenv("CA_PATH", "").strip()

app = Flask(__name__, static_folder="static", template_folder="templates")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
app.config["APP_BASE_URL"] = os.getenv("APP_BASE_URL", "")

engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": 300,   # TiDB Cloud Starter 向け
}

if DATABASE_URL.startswith("mysql+pymysql://") and CA_PATH:
    engine_options["connect_args"] = {
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
        "ssl_ca": CA_PATH,
    }

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

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
    with app.app_context():
        db.create_all()

@app.before_request
def before_request():
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

    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "http://" + url

    if not validators.url(url):
        flash("URL の形式が正しくありません。", "danger")
        return redirect(url_for("index"))

    existing = Link.query.filter_by(original_url=url).first()
    if existing:
        short_url = build_short_url(existing.short_code)
        return render_template("result.html", short_url=short_url, link=existing, title="Shortened")

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
    base = app.config.get("APP_BASE_URL")
    if base:
        return f"{base.rstrip('/')}/{code}"
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    host = request.headers.get("Host", request.host)
    return f"{scheme}://{host}/{code}"

@app.get("/<string:short_code>")
def resolve(short_code: str):
    link = Link.query.filter_by(short_code=short_code).first()
    if not link:
        return render_template("404.html"), 404

    Link.query.filter_by(id=link.id).update({Link.clicks: Link.clicks + 1})
    db.session.commit()
    return redirect(link.original_url, code=302)

@app.post("/links/<int:link_id>/delete")
def delete_link(link_id: int):
    link = Link.query.get(link_id)
    if not link:
        flash("対象のリンクが見つかりません。", "warning")
        return redirect(url_for("index"))
    db.session.delete(link)
    db.session.commit()
    flash("短縮リンクを削除しました。", "success")
    return redirect(url_for("index"))

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))