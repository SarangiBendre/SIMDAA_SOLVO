from sqlalchemy import Column, Integer, String
from app.database import Base

class Vote(Base):
    __tablename__ = "Votes"

    VoteID = Column(Integer, primary_key=True, index=True)
    AnswerID = Column(Integer)
    UserID = Column(Integer)
    VoteType = Column(Integer)