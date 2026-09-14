from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base


# ============================================================
# Answer Model
# ============================================================

class Answer(Base):
    __tablename__ = "Answers"

    AnswerID = Column(Integer, primary_key=True, index=True)
    QuestionID = Column(Integer)
    UserID = Column(Integer)
    AnswerText = Column(String)
    IsAccepted = Column(Boolean)
    Upvotes = Column(Integer)
    CreatedAt = Column(DateTime)
    UpdatedAt = Column(DateTime)


# ============================================================
# Vote Model
# ============================================================

class Vote(Base):
    __tablename__ = "Votes"

    VoteID = Column(Integer, primary_key=True, index=True)
    AnswerID = Column(Integer)
    UserID = Column(Integer)
    VoteType = Column(Integer)


class AnswerCreate(BaseModel):
    QuestionID: int
    UserID: int
    AnswerText: str


class CommentCreate(BaseModel):
    AnswerID: int
    UserID: int
    CommentText: str