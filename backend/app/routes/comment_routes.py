from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(
    prefix="/comments",
    tags=["Comments"]
)


# ============================================================
# Request Model
# ============================================================

class CommentCreate(BaseModel):
    AnswerID: int
    CommentText: str


# ============================================================
# POST /comments/
# Add Comment
# ============================================================

@router.post("/")
def create_comment(
    comment: CommentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Check Answer Exists
    answer = db.execute(
        text("""
            SELECT AnswerID
            FROM Answers
            WHERE AnswerID = :answer_id
        """),
        {
            "answer_id": comment.AnswerID
        }
    ).fetchone()

    if not answer:
        raise HTTPException(
            status_code=404,
            detail="Answer not found"
        )

    # Check User Exists
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

    # Insert Comment
    result = db.execute(
        text("""
            INSERT INTO Comments
            (
                AnswerID,
                UserID,
                CommentText,
                CreatedAt
            )
            OUTPUT
                INSERTED.CommentID,
                INSERTED.AnswerID,
                INSERTED.UserID,
                INSERTED.CommentText,
                INSERTED.CreatedAt
            VALUES
            (
                :answer_id,
                :user_id,
                :comment_text,
                GETDATE()
            )
        """),
        {
            "answer_id": comment.AnswerID,
            "user_id": current_user["UserID"],
            "comment_text": comment.CommentText
        }
    )

    new_comment = result.fetchone()

    db.commit()

    return {
        "message": "Comment added successfully",
        "CommentID": new_comment.CommentID,
        "AnswerID": new_comment.AnswerID,
        "UserID": new_comment.UserID,
        "CommentText": new_comment.CommentText,
        "CreatedAt": new_comment.CreatedAt
    }


# ============================================================
# GET /comments/answer/{answer_id}
# Get Comments For Answer
# ============================================================

@router.get("/answer/{answer_id}")
def get_comments_by_answer(
    answer_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Check Answer Exists
    answer = db.execute(
        text("""
            SELECT AnswerID
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

    comments = db.execute(
        text("""
            SELECT
                CommentID,
                AnswerID,
                UserID,
                CommentText,
                CreatedAt
            FROM Comments
            WHERE AnswerID = :answer_id
            ORDER BY CreatedAt ASC
        """),
        {
            "answer_id": answer_id
        }
    ).fetchall()

    return [
        {
            "CommentID": c.CommentID,
            "AnswerID": c.AnswerID,
            "UserID": c.UserID,
            "CommentText": c.CommentText,
            "CreatedAt": c.CreatedAt
        }
        for c in comments
    ]


# ============================================================
# DELETE /comments/{comment_id}
# Delete Own Comment
# ============================================================

@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    comment = db.execute(
        text("""
            SELECT
                CommentID,
                UserID
            FROM Comments
            WHERE CommentID = :comment_id
        """),
        {
            "comment_id": comment_id
        }
    ).fetchone()

    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )

    if comment.UserID != current_user["UserID"]:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own comments"
        )

    db.execute(
        text("""
            DELETE FROM Comments
            WHERE CommentID = :comment_id
        """),
        {
            "comment_id": comment_id
        }
    )

    db.commit()

    return {
        "message": "Comment deleted successfully"
    }
class CommentUpdate(BaseModel):
    CommentText:str

@router.get("/{comment_id}")
def get_comment(comment_id:int,current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.execute(text("SELECT * FROM Comments WHERE CommentID=:id"),{"id":comment_id}).fetchone()
    if not r: raise HTTPException(status_code=404,detail="Comment not found")
    return dict(r._mapping)

@router.put("/{comment_id}")
def update_comment(comment_id:int,payload:CommentUpdate,current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    db.execute(text("UPDATE Comments SET CommentText=:txt WHERE CommentID=:id AND UserID=:uid"),
    {"txt":payload.CommentText,"id":comment_id,"uid":current_user["UserID"]})
    db.commit()
    return {"message":"Comment updated successfully"}
