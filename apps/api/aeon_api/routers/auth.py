"""Login."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from aeon_api.db import get_session
from aeon_api.models import User, Workspace
from aeon_api.security import current_user, issue_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(body: LoginRequest, session: Session = Depends(get_session)) -> dict:
    user = session.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Unknown email or password.")
    workspace = session.scalar(select(Workspace).where(Workspace.owner_id == user.id))
    return {
        "token": issue_token(user.id),
        "user": {"id": user.id, "email": user.email, "display_name": user.display_name, "is_admin": user.is_admin},
        "workspace": {"id": workspace.id, "name": workspace.name} if workspace else None,
    }


@router.get("/me")
def me(user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict:
    workspace = session.scalar(select(Workspace).where(Workspace.owner_id == user.id))
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "is_admin": user.is_admin,
        "workspace": {"id": workspace.id, "name": workspace.name} if workspace else None,
    }
