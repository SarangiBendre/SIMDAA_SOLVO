from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel


from app.database import get_db


router = APIRouter(
    prefix="/answers",
    tags=["Answers"]
)


# ============================================================
# Request Model - Create Answer
# ============================================================

class AnswerCreate(BaseModel):
    QuestionID: int
    UserID: int
    AnswerText: str


# ============================================================
# POST /answers/
# Create a new answer
# ============================================================

@router.post("/")
def create_answer(
    answer: AnswerCreate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Check whether question exists
    # --------------------------------------------------------

    question = db.execute(
        text("""
            SELECT QuestionID
            FROM Questions
            WHERE QuestionID = :question_id
        """),
        {
            "question_id": answer.QuestionID
        }
    ).fetchone()

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )


    # --------------------------------------------------------
    # Check whether user exists and is active
    # --------------------------------------------------------

    user = db.execute(
        text("""
            SELECT UserID
            FROM Users
            WHERE UserID = :user_id
              AND IsActive = 1
        """),
        {
            "user_id": answer.UserID
        }
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found or inactive"
        )


    # --------------------------------------------------------
    # Insert answer
    # --------------------------------------------------------

    result = db.execute(
        text("""
            INSERT INTO Answers
            (
                QuestionID,
                UserID,
                AnswerText,
                IsAccepted,
                Upvotes,
                CreatedAt
            )
            OUTPUT
                INSERTED.AnswerID,
                INSERTED.QuestionID,
                INSERTED.UserID,
                INSERTED.AnswerText,
                INSERTED.IsAccepted,
                INSERTED.Upvotes,
                INSERTED.CreatedAt,
                INSERTED.UpdatedAt
            VALUES
            (
                :question_id,
                :user_id,
                :answer_text,
                0,
                0,
                GETDATE()
            )
        """),
        {
            "question_id": answer.QuestionID,
            "user_id": answer.UserID,
            "answer_text": answer.AnswerText
        }
    )

    new_answer = result.fetchone()

    db.commit()


    return {
        "message": "Answer created successfully",
        "AnswerID": new_answer.AnswerID,
        "QuestionID": new_answer.QuestionID,
        "UserID": new_answer.UserID,
        "AnswerText": new_answer.AnswerText,
        "IsAccepted": new_answer.IsAccepted,
        "Upvotes": new_answer.Upvotes,
        "CreatedAt": new_answer.CreatedAt,
        "UpdatedAt": new_answer.UpdatedAt
    }


# ============================================================
# GET /answers/question/{question_id}
# Get all answers for a question
# ============================================================

@router.get("/question/{question_id}")
def get_answers_by_question(
    question_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Check whether question exists
    # --------------------------------------------------------

    question = db.execute(
        text("""
            SELECT QuestionID
            FROM Questions
            WHERE QuestionID = :question_id
        """),
        {
            "question_id": question_id
        }
    ).fetchone()

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )


    # --------------------------------------------------------
    # Get answers
    # Accepted answer appears first
    # Then highest upvotes
    # --------------------------------------------------------

    result = db.execute(
        text("""
            SELECT
                AnswerID,
                QuestionID,
                UserID,
                AnswerText,
                IsAccepted,
                Upvotes,
                CreatedAt,
                UpdatedAt
            FROM Answers
            WHERE QuestionID = :question_id
            ORDER BY
                IsAccepted DESC,
                Upvotes DESC,
                CreatedAt ASC
        """),
        {
            "question_id": question_id
        }
    )

    answers = result.fetchall()


    return [
        {
            "AnswerID": answer.AnswerID,
            "QuestionID": answer.QuestionID,
            "UserID": answer.UserID,
            "AnswerText": answer.AnswerText,
            "IsAccepted": answer.IsAccepted,
            "Upvotes": answer.Upvotes,
            "CreatedAt": answer.CreatedAt,
            "UpdatedAt": answer.UpdatedAt
        }
        for answer in answers
    ]


# ============================================================
# GET /answers/{answer_id}
# Get a single answer
# ============================================================

@router.get("/{answer_id}")
def get_answer(
    answer_id: int,
    db: Session = Depends(get_db)
):

    result = db.execute(
        text("""
            SELECT
                AnswerID,
                QuestionID,
                UserID,
                AnswerText,
                IsAccepted,
                Upvotes,
                CreatedAt,
                UpdatedAt
            FROM Answers
            WHERE AnswerID = :answer_id
        """),
        {
            "answer_id": answer_id
        }
    )

    answer = result.fetchone()


    if not answer:
        raise HTTPException(
            status_code=404,
            detail="Answer not found"
        )


    return {
        "AnswerID": answer.AnswerID,
        "QuestionID": answer.QuestionID,
        "UserID": answer.UserID,
        "AnswerText": answer.AnswerText,
        "IsAccepted": answer.IsAccepted,
        "Upvotes": answer.Upvotes,
        "CreatedAt": answer.CreatedAt,
        "UpdatedAt": answer.UpdatedAt
    }