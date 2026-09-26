from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Comment, Answer
from app.auth import get_current_user

router = APIRouter(prefix="/comments", tags=["Comments"])


class CommentCreate(BaseModel):
    AnswerID: int
    CommentText: str


class CommentUpdate(BaseModel):
    CommentText: str


def _serialize(c: Comment):
    return {
        "CommentID": c.CommentID,
        "AnswerID": c.AnswerID,
        "UserID": c.UserID,
        "AuthorName": c.answer and None,  # comments don't eager-load user; kept lightweight
        "CommentText": c.CommentText,
        "CreatedAt": c.CreatedAt,
    }


@router.post("/")
def create_comment(comment: CommentCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    answer = db.query(Answer).filter(Answer.AnswerID == comment.AnswerID).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    new_comment = Comment(
        AnswerID=comment.AnswerID,
        UserID=current_user["UserID"],
        CommentText=comment.CommentText,
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {"message": "Comment added successfully", **_serialize(new_comment)}


@router.get("/answer/{answer_id}")
def get_comments_by_answer(answer_id: int, db: Session = Depends(get_db)):
    answer = db.query(Answer).filter(Answer.AnswerID == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    comments = db.query(Comment).filter(Comment.AnswerID == answer_id).order_by(Comment.CreatedAt.asc()).all()
    return [_serialize(c) for c in comments]


@router.get("/{comment_id}")
def get_comment(comment_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.CommentID == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return _serialize(comment)


@router.put("/{comment_id}")
def update_comment(comment_id: int, payload: CommentUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.CommentID == comment_id, Comment.UserID == current_user["UserID"]).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.CommentText = payload.CommentText
    db.commit()
    return {"message": "Comment updated successfully"}


@router.delete("/{comment_id}")
def delete_comment(comment_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.CommentID == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.UserID != current_user["UserID"]:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}
