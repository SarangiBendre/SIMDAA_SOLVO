from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Vote, Answer
from app.auth import get_current_user

router = APIRouter(
    prefix="/votes",
    tags=["Votes"]
)


# ============================================================
# Request Model
# ============================================================

class VoteCreate(BaseModel):
    AnswerID: int
    VoteType: int  # 1 = Upvote, -1 = Downvote


# ============================================================
# POST /votes/
# Create Vote
# ============================================================

@router.post("/")
def create_vote(
    vote: VoteCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Validate Vote Type
    if vote.VoteType not in [1, -1]:
        raise HTTPException(
            status_code=400,
            detail="VoteType must be 1 or -1"
        )

    # Check Answer Exists
    answer = (
        db.query(Answer)
        .filter(Answer.AnswerID == vote.AnswerID)
        .first()
    )

    if not answer:
        raise HTTPException(
            status_code=404,
            detail="Answer not found"
        )

    # Check Existing Vote
    existing_vote = (
        db.query(Vote)
        .filter(
            Vote.AnswerID == vote.AnswerID,
            Vote.UserID == current_user["UserID"]
        )
        .first()
    )

    if existing_vote:
        raise HTTPException(
            status_code=400,
            detail="You have already voted on this answer"
        )

    # Create Vote
    new_vote = Vote(
        AnswerID=vote.AnswerID,
        UserID=current_user["UserID"],
        VoteType=vote.VoteType
    )

    db.add(new_vote)

    # Update Answer Vote Count
    answer.Upvotes += vote.VoteType

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
    current_user=Depends(get_current_user),
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


# ============================================================
# GET /votes/count/{answer_id}
# Get Vote Count
# ============================================================

@router.get("/count/{answer_id}")
def get_vote_count(
    answer_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    answer = (
        db.query(Answer)
        .filter(Answer.AnswerID == answer_id)
        .first()
    )

    if not answer:
        raise HTTPException(
            status_code=404,
            detail="Answer not found"
        )

    votes = (
        db.query(Vote)
        .filter(Vote.AnswerID == answer_id)
        .all()
    )

    total_votes = sum(vote.VoteType for vote in votes)

    return {
        "AnswerID": answer_id,
        "TotalVotes": total_votes,
        "UpvotesColumn": answer.Upvotes
    }