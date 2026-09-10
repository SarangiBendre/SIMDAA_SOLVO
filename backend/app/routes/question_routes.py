from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel


from app.database import get_db


router = APIRouter(
    prefix="/questions",
    tags=["Questions"]
)


# ============================================================
# Request Model - Create Question
# ============================================================

class QuestionCreate(BaseModel):
    UserID: int
    CategoryID: int
    Title: str
    Description: str
    AttachmentPath: str | None = None


# ============================================================
# POST /questions/
# Create a new question
# ============================================================

@router.post("/")
def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db)
):

    # Check whether user exists
    user = db.execute(
        text("""
            SELECT UserID
            FROM Users
            WHERE UserID = :user_id
              AND IsActive = 1
        """),
        {
            "user_id": question.UserID
        }
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found or inactive"
        )


    # Check whether category exists
    category = db.execute(
        text("""
            SELECT CategoryID
            FROM Categories
            WHERE CategoryID = :category_id
              AND IsActive = 1
        """),
        {
            "category_id": question.CategoryID
        }
    ).fetchone()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found or inactive"
        )


    # Insert question
    result = db.execute(
        text("""
            INSERT INTO Questions
            (
                UserID,
                CategoryID,
                StatusID,
                Title,
                Description,
                AttachmentPath,
                ViewsCount,
                CreatedAt
            )
            OUTPUT
                INSERTED.QuestionID,
                INSERTED.UserID,
                INSERTED.CategoryID,
                INSERTED.StatusID,
                INSERTED.Title,
                INSERTED.Description,
                INSERTED.AttachmentPath,
                INSERTED.ViewsCount,
                INSERTED.CreatedAt
            VALUES
            (
                :user_id,
                :category_id,
                1,
                :title,
                :description,
                :attachment_path,
                0,
                GETDATE()
            )
        """),
        {
            "user_id": question.UserID,
            "category_id": question.CategoryID,
            "title": question.Title,
            "description": question.Description,
            "attachment_path": question.AttachmentPath
        }
    )

    new_question = result.fetchone()

    db.commit()


    return {
        "message": "Question created successfully",
        "QuestionID": new_question.QuestionID,
        "UserID": new_question.UserID,
        "CategoryID": new_question.CategoryID,
        "StatusID": new_question.StatusID,
        "Title": new_question.Title,
        "Description": new_question.Description,
        "AttachmentPath": new_question.AttachmentPath,
        "ViewsCount": new_question.ViewsCount,
        "CreatedAt": new_question.CreatedAt
    }


# ============================================================
# GET /questions/
# Get all questions
# ============================================================

@router.get("/")
def get_questions(
    db: Session = Depends(get_db)
):

    result = db.execute(
        text("""
            SELECT
                QuestionID,
                UserID,
                CategoryID,
                StatusID,
                Title,
                Description,
                AttachmentPath,
                ViewsCount,
                CreatedAt,
                UpdatedAt
            FROM Questions
            ORDER BY CreatedAt DESC
        """)
    )

    questions = result.fetchall()


    return [
        {
            "QuestionID": question.QuestionID,
            "UserID": question.UserID,
            "CategoryID": question.CategoryID,
            "StatusID": question.StatusID,
            "Title": question.Title,
            "Description": question.Description,
            "AttachmentPath": question.AttachmentPath,
            "ViewsCount": question.ViewsCount,
            "CreatedAt": question.CreatedAt,
            "UpdatedAt": question.UpdatedAt
        }
        for question in questions
    ]


# ============================================================
# GET /questions/{question_id}
# Get a single question
# ============================================================

@router.get("/{question_id}")
def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):

    result = db.execute(
        text("""
            SELECT
                QuestionID,
                UserID,
                CategoryID,
                StatusID,
                Title,
                Description,
                AttachmentPath,
                ViewsCount,
                CreatedAt,
                UpdatedAt
            FROM Questions
            WHERE QuestionID = :question_id
        """),
        {
            "question_id": question_id
        }
    )

    question = result.fetchone()


    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )


    return {
        "QuestionID": question.QuestionID,
        "UserID": question.UserID,
        "CategoryID": question.CategoryID,
        "StatusID": question.StatusID,
        "Title": question.Title,
        "Description": question.Description,
        "AttachmentPath": question.AttachmentPath,
        "ViewsCount": question.ViewsCount,
        "CreatedAt": question.CreatedAt,
        "UpdatedAt": question.UpdatedAt
    }