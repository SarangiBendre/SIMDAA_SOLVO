from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, PasswordResetToken
from app.auth import verify_password, hash_password, create_access_token, get_current_user
from app.Services.email_service import send_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

RESET_CODE_EXPIRY_MINUTES = 15


class LoginRequest(BaseModel):
    Username: str
    Password: str


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.Username == payload.Username, User.IsActive.is_(True))
        .first()
    )

    if not user or not verify_password(payload.Password, user.PasswordHash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user.LastLogin = datetime.utcnow()
    db.commit()

    token = create_access_token({
        "UserID": user.UserID,
        "Username": user.Username,
        "RoleID": user.RoleID,
    })

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "UserID": user.UserID,
            "Username": user.Username,
            "FullName": user.FullName,
            "Email": user.Email,
            "RoleID": user.RoleID,
            "Points": user.Points,
            "Level": user.Level,
        }
    }


@router.get("/me")
def me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserID == current_user["UserID"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "UserID": user.UserID,
        "Username": user.Username,
        "FullName": user.FullName,
        "Email": user.Email,
        "Department": user.Department,
        "RoleID": user.RoleID,
        "Points": user.Points,
        "Level": user.Level,
    }


class ChangePasswordRequest(BaseModel):
    CurrentPassword: str
    NewPassword: str


@router.put("/change-password")
def change_password(payload: ChangePasswordRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Self-service password change for a logged-in user - requires the
    current password as proof of identity."""

    user = db.query(User).filter(User.UserID == current_user["UserID"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(payload.CurrentPassword, user.PasswordHash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(payload.NewPassword) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    user.PasswordHash = hash_password(payload.NewPassword)
    db.commit()

    return {"message": "Password updated successfully"}


def mask_email(email: str) -> str:
    """Turns 'sarangi.bendre@gmail.com' into 'sa***@g***.com' - enough
    for the user to recognize it's their inbox, without displaying the
    full address."""

    local, _, domain = email.partition("@")
    domain_name, dot, tld = domain.partition(".")

    masked_local = (local[:2] + "***") if len(local) > 2 else (local[:1] + "***")
    masked_domain = (domain_name[:1] + "***") if domain_name else "***"

    return f"{masked_local}@{masked_domain}.{tld}" if tld else f"{masked_local}@{masked_domain}"


class ForgotPasswordRequest(BaseModel):
    Username: str


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Starts a password reset: emails a 6-digit verification code to
    the email already on file for this username - the user never types
    an email address, and only a masked version of it is ever shown
    back to them."""

    user = db.query(User).filter(User.Username == payload.Username, User.IsActive.is_(True)).first()

    if not user:
        return {"message": "If that username exists, a verification code has been sent to the email on file."}

    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(PasswordResetToken(
        UserID=user.UserID,
        Code=code,
        ExpiresAt=datetime.utcnow() + timedelta(minutes=RESET_CODE_EXPIRY_MINUTES),
    ))
    db.commit()

    send_email(
        user.Email,
        "Your SIMDAA SOLVO password reset code",
        f"Your verification code is: {code}\n\n"
        f"It expires in {RESET_CODE_EXPIRY_MINUTES} minutes. "
        "If you didn't request this, you can safely ignore this email.",
    )

    return {
        "message": f"A verification code has been sent to {mask_email(user.Email)}.",
        "MaskedEmail": mask_email(user.Email),
    }


class ResetPasswordRequest(BaseModel):
    Username: str
    Code: str
    NewPassword: str


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.Username == payload.Username, User.IsActive.is_(True)).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or verification code")

    token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.UserID == user.UserID,
            PasswordResetToken.Code == payload.Code,
            PasswordResetToken.Used.is_(False),
        )
        .order_by(PasswordResetToken.CreatedAt.desc())
        .first()
    )

    if not token or token.ExpiresAt < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    if len(payload.NewPassword) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    user.PasswordHash = hash_password(payload.NewPassword)
    token.Used = True
    db.commit()

    return {"message": "Password reset successfully - you can now log in with your new password."}
