# Python Backend Without a Framework
## Building HTTP Endpoints, Database Sessions, and Migrations

This guide documents the exact patterns used in this project. Everything here
is battle-tested and working. Copy-paste freely into new projects.

---

## Stack

| Concern | Library | Install |
|---------|---------|---------|
| HTTP server | `aiohttp` | `uv add aiohttp` |
| ORM / models | `sqlmodel` | `uv add sqlmodel` |
| Sync DB driver | `psycopg2-binary` | `uv add psycopg2-binary` |
| Async DB driver | `asyncpg` | `uv add asyncpg` |
| Migrations | `alembic` | `uv add alembic` |
| Config / env | `pydantic-settings` | `uv add pydantic-settings` |
| Password hashing | `passlib[bcrypt]` + `bcrypt==4.0.1` | `uv add "passlib[bcrypt]" "bcrypt==4.0.1"` |
| JWT tokens | `python-jose[cryptography]` | `uv add "python-jose[cryptography]"` |
| Logging | `loguru` | `uv add loguru` |

> **bcrypt version matters.** Pin `bcrypt==4.0.1`. Version 5+ breaks passlib's
> internal version detection and raises `ValueError` on every hash call.

---

## Project Layout

```
myproject/
├── app/
│   ├── __init__.py
│   ├── server.py          # aiohttp app + route handlers
│   ├── main.py            # CLI entry point (click)
│   ├── config/
│   │   ├── config.py      # Pydantic Settings
│   │   ├── database.py    # engines + session factories
│   │   └── security.py    # bcrypt + JWT helpers
│   ├── models/
│   │   ├── __init__.py    # imports all models (required for Alembic)
│   │   └── user.py        # SQLModel table definitions
│   └── services/
│       └── auth_service.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── .env
└── pyproject.toml
```

---

## Part 1 — Configuration

### `.env`

```dotenv
# App
APP_NAME=myproject
DEBUG=false
LOG_LEVEL=INFO

# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=mydb

# Security
SECRET_KEY=generate_with_openssl_rand_hex_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a secret key:
```bash
openssl rand -hex 32
```

### `app/config/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "myproject"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
```

**Key points:**
- `extra="ignore"` prevents errors when `.env` has keys not declared in the class.
- Required fields (no default) raise `ValidationError` at startup if missing.
- `@property` for derived values like DB URLs — not stored in `.env`, computed on access.
- The module-level `settings = Settings()` singleton is imported everywhere.

---

## Part 2 — Database Sessions

### `app/config/database.py`

```python
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import Session

from app.config.config import settings

# Sync engine — used for regular blocking operations
sync_engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,   # test connection before use
    echo=settings.DEBUG,  # log SQL when DEBUG=true
)

# Async engine — used for async handlers
async_engine = create_async_engine(
    settings.async_database_url,
    poolclass=NullPool,   # no pool — safe for async contexts
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)


@contextmanager
def get_sync_session():
    """
    Sync context manager. Use with `with get_sync_session() as session:`.
    Commits on success, rolls back on any exception.
    expire_on_commit=False keeps objects accessible after commit.
    """
    with Session(sync_engine, expire_on_commit=False) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


@asynccontextmanager
async def get_async_session():
    """
    Async context manager. Use with `async with get_async_session() as session:`.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

### Why `Session` from `sqlmodel` not `sqlalchemy.orm`?

SQLAlchemy's `Session` does **not** have `.exec()`. SQLModel's `Session` wraps it
and adds `.exec()` which works with SQLModel's typed `select()` statements.

```python
# WRONG — AttributeError: 'Session' object has no attribute 'exec'
from sqlalchemy.orm import Session

# CORRECT
from sqlmodel import Session
```

### Why `expire_on_commit=False`?

By default SQLAlchemy expires all object attributes after `commit()`. If you
access `user.id` after the session commits (e.g. to return it in a response),
you get `DetachedInstanceError`. Setting `expire_on_commit=False` keeps the
last-known values accessible after commit.

```python
# Without expire_on_commit=False — BREAKS
with get_sync_session() as session:
    user = User(email="a@b.com", ...)
    session.add(user)
    session.commit()
# session is now closed — accessing user.id raises DetachedInstanceError

# With expire_on_commit=False — WORKS
with get_sync_session() as session:
    user = User(email="a@b.com", ...)
    session.add(user)
    session.commit()
return {"id": user.id}  # safe
```

### Using sessions in services

```python
from sqlmodel import Session, select
from app.models.user import User


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def create_user(session: Session, email: str, username: str) -> User:
    user = User(email=email, username=username)
    session.add(user)
    session.commit()
    session.refresh(user)  # reload from DB to get generated id
    return user


def update_user(session: Session, user_id: int, full_name: str) -> User | None:
    user = session.get(User, user_id)  # get by primary key
    if not user:
        return None
    user.full_name = full_name
    session.add(user)
    session.commit()
    return user


def delete_user(session: Session, user_id: int) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True
```

### Calling from a handler

```python
from app.config.database import get_sync_session

with get_sync_session() as session:
    user = create_user(session, email="a@b.com", username="alice")
    print(user.id)  # safe — expire_on_commit=False
```

---

## Part 3 — SQLModel Data Models

### Defining a table

```python
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import sqlalchemy as sa


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Composite index (multi-column)

```python
class StockData(SQLModel, table=True):
    __tablename__ = "stock_data"
    __table_args__ = (
        sa.Index("ix_stock_data_symbol_date", "symbol_id", "date"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id")
    date: date
    close: float
```

### Foreign keys

```python
class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)  # FK syntax
    token: str = Field(unique=True, index=True)
```

### `app/models/__init__.py` — required for Alembic

```python
# Import every model here so Alembic can discover them during autogenerate
from app.models.user import User, UserSession
from app.models.stock import StockSymbol, StockData

__all__ = ["User", "UserSession", "StockSymbol", "StockData"]
```

---

## Part 4 — Alembic Migrations

### Initial setup

```bash
alembic init alembic
```

### `alembic.ini` — set a dummy URL

The real URL comes from `.env` via `env.py`. The `alembic.ini` value is
overridden at runtime, so use a placeholder:

```ini
sqlalchemy.url = postgresql+psycopg2://placeholder/placeholder
```

Never put real credentials in `alembic.ini` — it's committed to git.

### `alembic/env.py` — wire to your Settings

Add these lines near the top, **before** `target_metadata`:

```python
import app.models  # noqa: F401 — registers all SQLModel tables
from sqlmodel import SQLModel
from app.config.config import settings

config = context.config

# Override URL from .env — this is the critical line
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

# ...existing logging setup...

target_metadata = SQLModel.metadata  # replaces `target_metadata = None`
```

**Why `import app.models`?** Alembic's autogenerate scans `SQLModel.metadata`
for table definitions. Tables only appear in metadata after their class is
imported. This import triggers all model registrations.

### `alembic/script.py.mako` — add sqlmodel import

Autogenerated migrations use `sqlmodel.sql.sqltypes.AutoString()` for string
columns. Without the import they fail with `NameError: name 'sqlmodel' is not
defined`. Add it to the template so every future migration includes it:

```mako
from alembic import op
import sqlalchemy as sa
import sqlmodel          # ← add this line
${imports if imports else ""}
```

### Workflow

```bash
# 1. Create the database first (one-time)
python -c "
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
conn = psycopg2.connect(host='localhost', user='postgres', password='pw', dbname='postgres')
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
conn.cursor().execute('CREATE DATABASE mydb')
conn.close()
"

# 2. Generate migration from your models
alembic revision --autogenerate -m "initial_schema"

# 3. Apply migration
alembic upgrade head

# 4. After changing a model, generate a new migration
alembic revision --autogenerate -m "add_column_x"
alembic upgrade head

# 5. Roll back one step
alembic downgrade -1

# 6. Check current revision
alembic current

# 7. View history
alembic history
```

### Common autogenerate gotcha

If you add a model but forget to import it in `app/models/__init__.py`,
autogenerate won't detect it. Always add new models to `__init__.py`.

---

## Part 5 — HTTP Server with aiohttp

### Minimal server structure

```python
# app/server.py
import json
from aiohttp import web
from app.config.database import get_sync_session
from app.utils.logger import logger


# ── response helpers ──────────────────────────────────────────────────────────

def _json(data, status=200):
    """Return a JSON response. `default=str` handles dates and decimals."""
    return web.Response(
        text=json.dumps(data, default=str),
        content_type="application/json",
        status=status,
    )

def _err(msg, status=400):
    return _json({"error": msg}, status)


# ── CORS middleware ───────────────────────────────────────────────────────────

def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        return _cors(web.Response(status=204))
    response = await handler(request)
    return _cors(response)


# ── route handlers ────────────────────────────────────────────────────────────

async def get_user(request):
    user_id = int(request.match_info["id"])
    from app.models.user import User
    with get_sync_session() as session:
        user = session.get(User, user_id)
    if not user:
        return _err("User not found", 404)
    return _json({"id": user.id, "username": user.username, "email": user.email})


async def create_user(request):
    try:
        body = await request.json()
        from app.services.auth_service import register_user
        with get_sync_session() as session:
            user = register_user(session, **body)
        return _json({"id": user.id, "username": user.username}, status=201)
    except ValueError as e:
        return _err(str(e), 400)
    except Exception as e:
        logger.error(f"create_user error: {e}")
        return _err("Internal server error", 500)


async def list_items(request):
    # Query params: /items?page=1&limit=20
    page = int(request.rel_url.query.get("page", 1))
    limit = int(request.rel_url.query.get("limit", 20))
    return _json({"page": page, "limit": limit, "items": []})


# ── app factory ───────────────────────────────────────────────────────────────

def create_app():
    app = web.Application(middlewares=[cors_middleware])

    # Route registration
    app.router.add_get("/users/{id}", get_user)
    app.router.add_post("/users", create_user)
    app.router.add_get("/items", list_items)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8000)
```

### Handler patterns

```python
# GET with path param
async def get_item(request):
    item_id = request.match_info["id"]          # /items/{id}

# GET with query params
async def list_items(request):
    q = request.rel_url.query.get("q", "")      # /items?q=foo
    page = int(request.rel_url.query.get("page", 1))

# POST with JSON body
async def create_item(request):
    body = await request.json()                  # parse JSON body
    name = body.get("name")

# Auth header
async def protected(request):
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
```

### Route patterns

```python
app.router.add_get("/items", list_items)
app.router.add_get("/items/{id}", get_item)
app.router.add_post("/items", create_item)
app.router.add_post("/items/{id}/publish", publish_item)
app.router.add_delete("/items/{id}", delete_item)
```

### Running the server

```bash
# Direct
python -m app.server

# As a module entry point (add to pyproject.toml)
# [project.scripts]
# serve = "app.server:main"
```

---

## Part 6 — Security (Passwords + JWT)

### `app/config/security.py`

```python
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.config.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    # Raises jose.JWTError on invalid/expired token
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
```

### Auth service pattern

```python
from sqlmodel import Session, select
from jose import JWTError
from app.models.user import User, UserSession
from app.config.security import hash_password, verify_password, create_access_token, decode_access_token


def register_user(session: Session, email: str, username: str, password: str) -> User:
    existing = session.exec(
        select(User).where((User.email == email) | (User.username == username))
    ).first()
    if existing:
        raise ValueError("Email or username already registered")
    user = User(email=email, username=username, hashed_password=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login_user(session: Session, username_or_email: str, password: str) -> tuple[str, UserSession]:
    user = session.exec(
        select(User).where(
            (User.username == username_or_email) | (User.email == username_or_email)
        )
    ).first()
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")
    token = create_access_token({"user_id": user.id, "username": user.username})
    # store session in DB...
    return token, user_session


def verify_token(session: Session, token: str) -> User:
    try:
        payload = decode_access_token(token)
    except JWTError as e:
        raise PermissionError(f"Invalid token: {e}") from e
    user = session.get(User, payload["user_id"])
    if not user:
        raise PermissionError("User not found")
    return user
```

---

## Part 7 — Testing Endpoints

### With curl

```bash
# POST with JSON body
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Pass1234!"}'

# GET with query params
curl -s "http://localhost:8000/stocks/AAPL/data?start=2026-01-01&end=2026-04-01"

# GET with path param
curl -s "http://localhost:8000/users/1"

# POST with auth header
curl -s -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer eyJhbGci..."

# Capture token from login response
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"testuser","password":"Pass1234!"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")

# Use captured token
curl -s -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

### With Python (requests)

```python
import requests

BASE = "http://localhost:8000"

# Register
r = requests.post(f"{BASE}/auth/register", json={
    "email": "test@example.com",
    "username": "testuser",
    "password": "Pass1234!",
})
assert r.status_code == 200, r.json()
print(r.json())  # {"id": 1, "username": "testuser", "email": "test@example.com"}

# Login
r = requests.post(f"{BASE}/auth/login", json={
    "username_or_email": "testuser",
    "password": "Pass1234!",
})
token = r.json()["token"]

# Authenticated request
r = requests.post(f"{BASE}/auth/logout", headers={"Authorization": f"Bearer {token}"})
print(r.json())  # {"message": "Logged out"}

# GET with params
r = requests.get(f"{BASE}/stocks/AAPL/data", params={"start": "2026-01-01", "end": "2026-04-01"})
data = r.json()
print(f"{len(data['data'])} records")
```

### With pytest

```python
# tests/test_endpoints.py
import pytest
import requests

BASE = "http://localhost:8000"


@pytest.fixture(scope="session")
def auth_token():
    requests.post(f"{BASE}/auth/register", json={
        "email": "pytest@example.com", "username": "pytestuser", "password": "Test1234!"
    })
    r = requests.post(f"{BASE}/auth/login", json={
        "username_or_email": "pytestuser", "password": "Test1234!"
    })
    return r.json()["token"]


def test_register_duplicate():
    r = requests.post(f"{BASE}/auth/register", json={
        "email": "pytest@example.com", "username": "pytestuser", "password": "Test1234!"
    })
    assert r.status_code == 400
    assert "already registered" in r.json()["error"]


def test_login_bad_password():
    r = requests.post(f"{BASE}/auth/login", json={
        "username_or_email": "pytestuser", "password": "wrongpassword"
    })
    assert r.status_code == 401
    assert r.json()["error"] == "Invalid credentials"


def test_stock_price():
    r = requests.get(f"{BASE}/stocks/AAPL/price")
    assert r.status_code == 200
    assert r.json()["price"] > 0


def test_symbol_search():
    r = requests.get(f"{BASE}/symbols/search", params={"q": "AAPL"})
    assert r.status_code == 200
    assert isinstance(r.json()["results"], list)
```

Run:
```bash
# Start server first, then:
source .venv/bin/activate
pytest tests/test_endpoints.py -v
```

### With aiohttp test client (no running server needed)

```python
# tests/test_server.py
import pytest
from aiohttp.test_utils import TestClient, TestServer
from app.server import create_app


@pytest.fixture
async def client():
    app = create_app()
    async with TestClient(TestServer(app)) as client:
        yield client


async def test_register(client):
    resp = await client.post("/auth/register", json={
        "email": "unit@test.com", "username": "unituser", "password": "Pass1234!"
    })
    assert resp.status == 200
    data = await resp.json()
    assert data["username"] == "unituser"


async def test_missing_query_param(client):
    resp = await client.get("/symbols/search")  # missing ?q=
    assert resp.status == 400
```

Run:
```bash
pytest tests/test_server.py -v --asyncio-mode=auto
# requires: uv add pytest-asyncio
```

---

## Part 8 — Common Bugs and Fixes

### `AttributeError: 'Session' object has no attribute 'exec'`

**Cause:** Using `sqlalchemy.orm.Session` instead of `sqlmodel.Session`.

```python
# Wrong
from sqlalchemy.orm import Session

# Correct
from sqlmodel import Session
```

### `DetachedInstanceError` after commit

**Cause:** Accessing model attributes after the session closes.

```python
# Fix: set expire_on_commit=False on the session
with Session(engine, expire_on_commit=False) as session:
    ...
```

### `ValueError: password cannot be longer than 72 bytes`

**Cause:** `bcrypt` version 5+ is incompatible with `passlib`.

```bash
uv add "bcrypt==4.0.1"
```

### `NameError: name 'sqlmodel' is not defined` in migration

**Cause:** Autogenerated migration uses `sqlmodel.sql.sqltypes.AutoString()` but
doesn't import `sqlmodel`.

**Fix 1:** Add `import sqlmodel` to the generated migration file.

**Fix 2 (permanent):** Add `import sqlmodel` to `alembic/script.py.mako` so all
future migrations include it automatically.

### `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:driver`

**Cause:** `alembic.ini` has the placeholder URL `driver://user:pass@localhost/dbname`
and `env.py` isn't overriding it.

**Fix:** In `alembic/env.py`, add:
```python
from app.config.config import settings
config.set_main_option("sqlalchemy.url", settings.sync_database_url)
```
And set `alembic.ini` to a valid dummy:
```ini
sqlalchemy.url = postgresql+psycopg2://placeholder/placeholder
```

### Alembic doesn't detect new tables

**Cause:** Model class not imported before autogenerate runs.

**Fix:** Import all models in `app/models/__init__.py` and import that module in
`alembic/env.py`:
```python
import app.models  # noqa: F401
```

### CORS errors from browser frontend

**Cause:** No CORS headers on responses.

**Fix:** Add the middleware shown in Part 5. Handle `OPTIONS` preflight requests
by returning `204` with the CORS headers.

---

## Part 9 — Quick Reference

### Session operations

```python
from sqlmodel import Session, select

# Get by primary key
user = session.get(User, user_id)

# Query with filter
user = session.exec(select(User).where(User.email == email)).first()

# Query multiple
users = session.exec(select(User).where(User.is_active == True)).all()

# Query with OR
user = session.exec(
    select(User).where((User.email == val) | (User.username == val))
).first()

# Query with AND (multiple .where() calls)
records = session.exec(
    select(StockData)
    .where(StockData.symbol_id == sid)
    .where(StockData.date >= start)
    .where(StockData.date <= end)
    .order_by(StockData.date)
).all()

# Insert
obj = MyModel(field="value")
session.add(obj)
session.commit()
session.refresh(obj)  # reload generated fields (id, created_at, etc.)

# Update
obj = session.get(MyModel, obj_id)
obj.field = "new_value"
session.add(obj)
session.commit()

# Delete
obj = session.get(MyModel, obj_id)
session.delete(obj)
session.commit()

# Upsert pattern (check-then-insert)
existing = session.exec(select(MyModel).where(MyModel.key == key)).first()
if existing:
    existing.value = new_value
    session.add(existing)
else:
    session.add(MyModel(key=key, value=new_value))
session.commit()
```

### aiohttp response helpers

```python
import json
from aiohttp import web

def _json(data, status=200):
    return web.Response(
        text=json.dumps(data, default=str),  # default=str handles dates
        content_type="application/json",
        status=status,
    )

def _err(msg, status=400):
    return _json({"error": msg}, status)
```

### Alembic commands

```bash
alembic revision --autogenerate -m "description"  # generate migration
alembic upgrade head                               # apply all pending
alembic downgrade -1                               # roll back one
alembic current                                    # show current revision
alembic history                                    # show all revisions
alembic stamp head                                 # mark as up-to-date without running
```
