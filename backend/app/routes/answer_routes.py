from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.database import get_db
from app.models import Answer
from app.auth import get_current_user

router = APIRouter(
    prefix="/answers",
    tags=["Answers"]
)


# ============================================================
# Request Model
# ============================================================

class AnswerCreate(BaseModel):
    QuestionID: int
    AnswerText: str


# ============================================================
# POST /answers/
# Create Answer
# ============================================================

@router.post("/")
def create_answer(
    answer: AnswerCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

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

    user = db.execute(
        text("""
            SELECT UserID
            FROM Users
            WHERE UserID = :user_id
              AND IsActive = 1
        """),
        {
            "user_id": current_user["UserID"]
        }
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found or inactive"
        )

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
            "user_id": current_user["UserID"],
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
# Get Answers By Question
# ============================================================

@router.get("/question/{question_id}")
def get_answers_by_question(
    question_id: int,
    db: Session = Depends(get_db)
):

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
# Get Single Answer
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


# ============================================================
# PUT /answers/{answer_id}/accept
# Accept Answer
# ============================================================

@router.put("/{answer_id}/accept")
def accept_answer(
    answer_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    answer = db.query(Answer).filter(
        Answer.AnswerID == answer_id
    ).first()

    if not answer:
        raise HTTPException(
            status_code=404,
            detail="Answer not found"
        )

    answer.IsAccepted = True

    db.commit()
    db.refresh(answer)

    return {
        "message": "Answer accepted successfully",
        "AnswerID": answer.AnswerID,
        "IsAccepted": answer.IsAccepted
    }


# ============================================================
# PUT /answers/{answer_id}/upvote
# Upvote Answer
# ============================================================

@router.put("/{answer_id}/upvote")
def upvote_answer(
    answer_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    answer = db.execute(
        text("""
            SELECT
                AnswerID,
                Upvotes
            FROM Answers
            WHERE AnswerID = :answer_id
        """),
        {
            "answer_id": answer_id
        }
    ).fetchone()

    if not answer:
        raise HTTPException(
            status_code=404,
            detail="Answer not found"
        )

    db.execute(
        text("""
            UPDATE Answers
            SET Upvotes = Upvotes + 1
            WHERE AnswerID = :answer_id
        """),
        {
            "answer_id": answer_id
        }
    )

    db.commit()

    updated_answer = db.execute(
        text("""
            SELECT
                AnswerID,
                Upvotes
            FROM Answers
            WHERE AnswerID = :answer_id
        """),
        {
            "answer_id": answer_id
        }
    ).fetchone()

    return {
        "message": "Answer upvoted successfully",
        "AnswerID": updated_answer.AnswerID,
        "Upvotes": updated_answer.Upvotes
    }
class AnswerUpdate(BaseModel):
    AnswerText:str

@router.put("/{answer_id}")
def update_answer(answer_id:int,payload:AnswerUpdate,current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    db.execute(text("UPDATE Answers SET AnswerText=:txt, UpdatedAt=GETDATE() WHERE AnswerID=:id AND UserID=:uid"),
    {"txt":payload.AnswerText,"id":answer_id,"uid":current_user["UserID"]})
    db.commit()
    return {"message":"Answer updated successfully"}

@router.delete("/{answer_id}")
def delete_answer(answer_id:int,current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    db.execute(text("DELETE FROM Answers WHERE AnswerID=:id AND UserID=:uid"),{"id":answer_id,"uid":current_user["UserID"]})
    db.commit()
    return {"message":"Answer deleted successfully"}
