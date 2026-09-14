from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from jose import jwt
import bcrypt

from ..database import engine

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

SECRET_KEY = "simdaa_secret_key"
ALGORITHM = "HS256"


# ============================================================
# Login Request Model
# ============================================================

class LoginRequest(BaseModel):
    Username: str
    Password: str


# ============================================================
# POST /auth/login
# ============================================================

@router.post("/login")
def login(user: LoginRequest):

    with engine.connect() as connection:

        db_user = connection.execute(
            text("""
                SELECT
                    UserID,
                    Username,
                    PasswordHash,
                    RoleID
                FROM Users
                WHERE Username = :username
                  AND IsActive = 1
            """),
            {
                "username": user.Username
            }
        ).first()

        if not db_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        try:
            valid_password = bcrypt.checkpw(
                user.Password.encode("utf-8"),
                db_user.PasswordHash.encode("utf-8")
            )
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Password hash error"
            )

        if not valid_password:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        # Update Last Login
        connection.execute(
            text("""
                UPDATE Users
                SET LastLogin = GETDATE()
                WHERE UserID = :user_id
            """),
            {
                "user_id": db_user.UserID
            }
        )

        connection.commit()

        payload = {
            "UserID": db_user.UserID,
            "Username": db_user.Username,
            "RoleID": db_user.RoleID
        }

        token = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        return {
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "UserID": db_user.UserID,
                "Username": db_user.Username,
                "RoleID": db_user.RoleID
            }
        }


# ============================================================
# GET /auth/test-token
# ============================================================

@router.get("/test-token")
def test_token():

    test_token = jwt.encode(
        {
            "UserID": 1,
            "Username": "test_user",
            "RoleID": 1
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "token": test_token
    }