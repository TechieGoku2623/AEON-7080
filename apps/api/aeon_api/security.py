"""Bearer tokens signed with the server secret. Passwords use PBKDF2."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from aeon_api.config import SECRET, TOKEN_HOURS
from aeon_api.db import get_session
from aeon_api.models import User, Workspace

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, _digest = stored.split("$", 1)
    return hmac.compare_digest(hash_password(password, salt), stored)


def issue_token(user_id: str) -> str:
    expiry = int(time.time()) + TOKEN_HOURS * 3600
    payload = f"{user_id}.{expiry}"
    signature = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def read_token(token: str) -> str:
    try:
        user_id, expiry, signature = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token.") from exc
    payload = f"{user_id}.{expiry}"
    expected = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid token.")
    if int(expiry) < time.time():
        raise HTTPException(status_code=401, detail="Token expired.")
    return user_id


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user_id = read_token(credentials.credentials)
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user.")
    return user


def current_workspace(
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> Workspace:
    workspace = session.scalar(select(Workspace).where(Workspace.owner_id == user.id))
    if workspace is None:
        raise HTTPException(status_code=403, detail="No workspace.")
    return workspace


def new_id() -> str:
    return str(uuid.uuid4())
