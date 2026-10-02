"""
Authentication helpers: password hashing and JWT handling.
"""

import os
import logging
from datetime import datetime, timedelta

import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.database import get_db

load_dotenv()

logger = logging.getLogger("simdaa.auth")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
if not SECRET_KEY:
    # Refusing to start is much safer than silently falling back to a
    # hardcoded default: a shared/well-known secret would let anyone
    # forge a valid token for any account, including an admin one, by
    # just signing their own JWT with the same known string. Better to
    # fail loudly at startup than run "securely-looking" but broken.
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Generate one with: "
        "python -c \"import secrets; print(secrets.token_urlsafe(48))\" "
        "and set it as an environment variable before starting the app."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

security = HTTPBearer()


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(payload: dict) -> str:
    to_encode = payload.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials.strip()

    if token.lower().startswith("bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # The token's RoleID/etc. are a snapshot from login time. Without
    # this check, deactivating or role-changing a user has no effect
    # until their token naturally expires (up to ACCESS_TOKEN_EXPIRE_HOURS
    # later) - an admin who deactivates a bad actor would expect that to
    # take effect immediately, not hours later. Import here (not at
    # module load) to avoid a circular import with app.models.
    from app.models import User

    user_id = payload.get("UserID")
    user = db.query(User).filter(User.UserID == user_id, User.IsActive.is_(True)).first() if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Always reflect the user's CURRENT role, not whatever was true when
    # they logged in - otherwise a demoted admin keeps admin access on
    # every request until they log out and back in.
    payload["RoleID"] = user.RoleID
    return payload


def require_role(*role_ids: int):
    """Dependency factory: restrict a route to specific RoleIDs."""

    def role_checker(current_user=Depends(get_current_user)):
        if current_user.get("RoleID") not in role_ids:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action"
            )
        return current_user

    return role_checker
