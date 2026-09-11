from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
import bcrypt

from ..database import engine


# Create Users router
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# ---------------------------------------------------------
# Request model for creating a user
# ---------------------------------------------------------

class UserCreate(BaseModel):
    RoleID: int
    Username: str
    Password: str
    FullName: str
    Email: str
    Department: str | None = None


# ---------------------------------------------------------
# GET /users/
# Get all users
# ---------------------------------------------------------

@router.get("/")
def get_users():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    UserID,
                    RoleID,
                    Username,
                    FullName,
                    Email,
                    Department,
                    IsActive,
                    CreatedAt,
                    UpdatedAt,
                    LastLogin
                FROM Users
                ORDER BY FullName
            """)
        )

        users = []

        for row in result:

            users.append({
                "UserID": row.UserID,
                "RoleID": row.RoleID,
                "Username": row.Username,
                "FullName": row.FullName,
                "Email": row.Email,
                "Department": row.Department,
                "IsActive": bool(row.IsActive),
                "CreatedAt": row.CreatedAt,
                "UpdatedAt": row.UpdatedAt,
                "LastLogin": row.LastLogin
            })

        return users



# ---------------------------------------------------------
# POST /users/
# Create a new user
# ---------------------------------------------------------

@router.post("/")
def create_user(user: UserCreate):

    # -----------------------------------------------------
    # Check if username already exists
    # -----------------------------------------------------

    with engine.connect() as connection:

        existing_username = connection.execute(
            text("""
                SELECT UserID
                FROM Users
                WHERE Username = :username
            """),
            {
                "username": user.Username
            }
        ).first()

        if existing_username:

            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )

        # -------------------------------------------------
        # Check if email already exists
        # -------------------------------------------------

        existing_email = connection.execute(
            text("""
                SELECT UserID
                FROM Users
                WHERE Email = :email
            """),
            {
                "email": user.Email
            }
        ).first()

        if existing_email:

            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )

        # -------------------------------------------------
        # Check if RoleID exists
        # -------------------------------------------------

        existing_role = connection.execute(
            text("""
                SELECT RoleID
                FROM Roles
                WHERE RoleID = :role_id
            """),
            {
                "role_id": user.RoleID
            }
        ).first()

        if not existing_role:

            raise HTTPException(
                status_code=400,
                detail="Invalid RoleID"
            )


    # -----------------------------------------------------
    # Hash password
    # -----------------------------------------------------

    password_hash = bcrypt.hashpw(
        user.Password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


    # -----------------------------------------------------
    # Insert user into database
    # -----------------------------------------------------

    with engine.begin() as connection:

        result = connection.execute(
            text("""
                INSERT INTO Users
                (
                    RoleID,
                    Username,
                    PasswordHash,
                    FullName,
                    Email,
                    Department
                )
                OUTPUT INSERTED.UserID
                VALUES
                (
                    :role_id,
                    :username,
                    :password_hash,
                    :full_name,
                    :email,
                    :department
                )
            """),
            {
                "role_id": user.RoleID,
                "username": user.Username,
                "password_hash": password_hash,
                "full_name": user.FullName,
                "email": user.Email,
                "department": user.Department
            }
        )

        user_id = result.scalar_one()


    # -----------------------------------------------------
    # Return successful response
    # -----------------------------------------------------

    return {
        "message": "User created successfully",
        "UserID": user_id,
        "Username": user.Username,
        "FullName": user.FullName,
        "Email": user.Email,
        "Department": user.Department,
        "RoleID": user.RoleID
    }

# ---------------------------------------------------------
# GET /users/profile/{user_id}
# User Profile API
# ---------------------------------------------------------

@router.get("/profile/{user_id}")
def get_user_profile(user_id: int):

    with engine.connect() as connection:

        # ---------------------------------------------
        # Get user details
        # ---------------------------------------------

        user = connection.execute(
            text("""
                SELECT
                    UserID,
                    Username,
                    FullName,
                    Email,
                    Department
                FROM Users
                WHERE UserID = :user_id
            """),
            {
                "user_id": user_id
            }
        ).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # ---------------------------------------------
        # Questions Asked
        # ---------------------------------------------

        questions_count = connection.execute(
            text("""
                SELECT COUNT(*) AS TotalQuestions
                FROM Questions
                WHERE UserID = :user_id
            """),
            {
                "user_id": user_id
            }
        ).scalar()

        # ---------------------------------------------
        # Answers Posted
        # ---------------------------------------------

        answers_count = connection.execute(
            text("""
                SELECT COUNT(*) AS TotalAnswers
                FROM Answers
                WHERE UserID = :user_id
            """),
            {
                "user_id": user_id
            }
        ).scalar()

        # ---------------------------------------------
        # Accepted Answers
        # ---------------------------------------------

        accepted_answers = connection.execute(
            text("""
                SELECT COUNT(*) AS AcceptedAnswers
                FROM Answers
                WHERE UserID = :user_id
                AND IsAccepted = 1
            """),
            {
                "user_id": user_id
            }
        ).scalar()

        return {
            "UserID": user.UserID,
            "Username": user.Username,
            "FullName": user.FullName,
            "Email": user.Email,
            "Department": user.Department,
            "QuestionsAsked": questions_count,
            "AnswersPosted": answers_count,
            "AcceptedAnswers": accepted_answers
        }


@router.get("/{user_id}")
def get_user(user_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    UserID,
                    RoleID,
                    Username,
                    FullName,
                    Email,
                    Department,
                    IsActive,
                    CreatedAt,
                    UpdatedAt,
                    LastLogin
                FROM Users
                WHERE UserID = :user_id
            """),
            {
                "user_id": user_id
            }
        ).first()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "UserID": result.UserID,
            "RoleID": result.RoleID,
            "Username": result.Username,
            "FullName": result.FullName,
            "Email": result.Email,
            "Department": result.Department,
            "IsActive": bool(result.IsActive),
            "CreatedAt": result.CreatedAt,
            "UpdatedAt": result.UpdatedAt,
            "LastLogin": result.LastLogin
        }