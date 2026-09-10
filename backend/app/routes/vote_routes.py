from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Vote

router = APIRouter(
    prefix="/votes",
    tags=["Votes"]
)


# ============================================================
# Request Model
# ============================================================

class VoteCreate(BaseModel):
    AnswerID: int
    UserID: int
    VoteType: int


# ============================================================
# POST /votes/
# Create Vote
# ============================================================

@router.post("/")
def create_vote(
    vote: VoteCreate,
    db: Session = Depends(get_db)
):
    new_vote = Vote(
        AnswerID=vote.AnswerID,
        UserID=vote.UserID,
        VoteType=vote.VoteType
    )

    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)

    return {
        "message": "Vote created successfully",
        "VoteID": new_vote.VoteID,
        "AnswerID": new_vote.AnswerID,
        "UserID": new_vote.UserID,
        "VoteType": new_vote.VoteType
    }


# ============================================================
# GET /votes/answer/{answer_id}
# Get Votes for Answer
# ============================================================

@router.get("/answer/{answer_id}")
def get_votes_by_answer(
    answer_id: int,
    db: Session = Depends(get_db)
):
    votes = (
        db.query(Vote)
        .filter(Vote.AnswerID == answer_id)
        .all()
    )

    return [
        {
            "VoteID": vote.VoteID,
            "AnswerID": vote.AnswerID,
            "UserID": vote.UserID,
            "VoteType": vote.VoteType
        }
        for vote in votes
    ]