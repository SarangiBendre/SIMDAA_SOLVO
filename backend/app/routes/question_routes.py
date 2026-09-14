from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.auth import get_current_user

from app.database import get_db
from app.Services.email_service import send_email


router = APIRouter(
    prefix="/questions",
    tags=["Questions"]
)


# ============================================================
# Request Model - Create Question
# ============================================================

class QuestionCreate(BaseModel):
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
    current_user=Depends(get_current_user),
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
            "user_id": current_user["UserID"]
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
            "user_id": current_user["UserID"],
            "category_id": question.CategoryID,
            "title": question.Title,
            "description": question.Description,
            "attachment_path": question.AttachmentPath
        }
    )

    new_question = result.fetchone()

    db.commit()

    # Get all active users except question creator
    active_users = db.execute(
        text("""
            SELECT Email
            FROM Users
            WHERE IsActive = 1
            AND UserID <> :current_user_id
        """),
        {
            "current_user_id": current_user["UserID"]
        }
    ).fetchall()

    # Send email to all active users
    for user_email in active_users:
        try:
            print(f"Sending email to: {user_email.Email}")

            send_email(
                user_email.Email,
                "New Question Posted - SIMDAA SOLVO",
                f"""
    A new question has been posted.

    Title:
    {new_question.Title}

    Description:
    {new_question.Description}

    Please login to SIMDAA SOLVO to view and answer.

    Regards,
    SIMDAA SOLVO Team
    """
            )

            print(f"Email sent to: {user_email.Email}")

        except Exception as e:
            print(f"Failed to send email to {user_email.Email}: {e}")

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
# GET /questions/search
# Search questions by keyword
# ============================================================

@router.get("/search")
def search_questions(
    keyword: str,
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
            WHERE
                Title LIKE :keyword
                OR Description LIKE :keyword
            ORDER BY CreatedAt DESC
        """),
        {
            "keyword": f"%{keyword}%"
        }
    )

    questions = result.fetchall()

    return [
        {
            "QuestionID": question.QuestionID,
            "Title": question.Title,
            "Description": question.Description,
            "ViewsCount": question.ViewsCount
        }
        for question in questions
    ]

# ============================================================
# GET /questions/{question_id}/details
# Get question with all answers
# ============================================================

@router.get("/{question_id}/details")
def get_question_details(
    question_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Get Question
    # --------------------------------------------------------

    question_result = db.execute(
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

    question = question_result.fetchone()

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )

    # --------------------------------------------------------
    # Get Answers
    # --------------------------------------------------------

    answers_result = db.execute(
        text("""
            SELECT
                AnswerID,
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
                Upvotes DESC
        """),
        {
            "question_id": question_id
        }
    )

    answers = answers_result.fetchall()

    # --------------------------------------------------------
    # Return Question + Answers
    # --------------------------------------------------------

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
        "UpdatedAt": question.UpdatedAt,
        "Answers": [
            {
                "AnswerID": answer.AnswerID,
                "UserID": answer.UserID,
                "AnswerText": answer.AnswerText,
                "IsAccepted": answer.IsAccepted,
                "Upvotes": answer.Upvotes,
                "CreatedAt": answer.CreatedAt,
                "UpdatedAt": answer.UpdatedAt
            }
            for answer in answers
        ]
    }



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




class QuestionUpdate(BaseModel):
    CategoryID: int | None = None
    Title: str | None = None
    Description: str | None = None
    AttachmentPath: str | None = None

@router.put("/{question_id}")
def update_question(question_id:int,payload:QuestionUpdate,current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    db.execute(text("""UPDATE Questions SET Title=COALESCE(:t,Title), Description=COALESCE(:d,Description), CategoryID=COALESCE(:c,CategoryID), AttachmentPath=COALESCE(:a,AttachmentPath), UpdatedAt=GETDATE() WHERE QuestionID=:id AND UserID=:uid"""),
    {"t":payload.Title,"d":payload.Description,"c":payload.CategoryID,"a":payload.AttachmentPath,"id":question_id,"uid":current_user["UserID"]})
    db.commit()
    return {"message":"Question updated successfully"}

@router.delete("/{question_id}")
def delete_question(question_id:int,current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    db.execute(text("DELETE FROM Questions WHERE QuestionID=:id AND UserID=:uid"),{"id":question_id,"uid":current_user["UserID"]})
    db.commit()
    return {"message":"Question deleted successfully"}
