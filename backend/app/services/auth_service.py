from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlmodel import Session, select
from jose import JWTError

from app.models.user import User, UserSession
from app.config.security import hash_password, verify_password, create_access_token, decode_access_token
from app.config.config import settings


def register_user(
    session: Session,
    email: str,
    username: str,
    password: str,
    full_name: Optional[str] = None,
) -> User:
    # Check for existing email/username
    existing = session.exec(
        select(User).where((User.email == email) | (User.username == username))
    ).first()
    if existing:
        raise ValueError("Email or username already registered")
    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login_user(
    session: Session,
    username_or_email: str,
    password: str,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[str, UserSession]:
    user = session.exec(
        select(User).where(
            (User.username == username_or_email) | (User.email == username_or_email)
        )
    ).first()
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")
    if not user.is_active:
        raise PermissionError("Account is inactive")
    token = create_access_token({"user_id": user.id, "username": user.username})
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    user_session = UserSession(
        user_id=user.id,
        token=token,
        ip_address=ip,
        user_agent=user_agent,
        expires_at=expires_at,
    )
    session.add(user_session)
    session.commit()
    session.refresh(user_session)
    return token, user_session


def verify_token(session: Session, token: str) -> User:
    try:
        payload = decode_access_token(token)
    except JWTError as e:
        raise PermissionError(f"Invalid token: {e}") from e
    user_session = session.exec(
        select(UserSession).where(UserSession.token == token)
    ).first()
    if not user_session:
        raise PermissionError("Session not found")
    if not user_session.is_active:
        raise PermissionError("Session is inactive")
    if user_session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise PermissionError("Session expired")
    user = session.get(User, payload["user_id"])
    if not user:
        raise PermissionError("User not found")
    return user


def logout_user(session: Session, token: str) -> None:
    user_session = session.exec(
        select(UserSession).where(UserSession.token == token)
    ).first()
    if user_session:
        user_session.is_active = False
        session.add(user_session)
        session.commit()
