"""
SQLAlchemy ORM models for SIMDAA SOLVO.
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, ForeignKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ============================================================
# Roles
# ============================================================

class Role(Base):
    __tablename__ = "roles"

    RoleID = Column(Integer, primary_key=True, index=True)
    RoleName = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


# Well-known role ids seeded on startup
# Well-known role ids seeded on startup - matches the 5 roles from the
# project requirements: Admin, Mentor/Senior, Employee, Intern, Trainee.
# Mentor and Admin get elevated privileges (notified of new questions,
# admin-only screens); Employee/Intern/Trainee all have the same base
# permissions (ask, answer, comment, vote) and exist as separate
# categories for reporting/identification purposes.
ROLE_ADMIN = 1
ROLE_MENTOR = 2
ROLE_EMPLOYEE = 3
ROLE_INTERN = 4
ROLE_TRAINEE = 5


# ============================================================
# Users
# ============================================================

class User(Base):
    __tablename__ = "users"

    UserID = Column(Integer, primary_key=True, index=True)
    RoleID = Column(Integer, ForeignKey("roles.RoleID"), nullable=False)
    Username = Column(String(100), unique=True, nullable=False, index=True)
    PasswordHash = Column(String(255), nullable=False)
    FullName = Column(String(150), nullable=False)
    Email = Column(String(150), unique=True, nullable=False)
    Department = Column(String(100), nullable=True)
    IsActive = Column(Boolean, default=True)
    Points = Column(Integer, default=0)
    Level = Column(String(50), default="Beginner")
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    LastLogin = Column(DateTime, nullable=True)

    role = relationship("Role", back_populates="users")
    questions = relationship("Question", back_populates="user")
    answers = relationship("Answer", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")


# ============================================================
# Categories
# ============================================================

class Category(Base):
    __tablename__ = "categories"

    CategoryID = Column(Integer, primary_key=True, index=True)
    CategoryName = Column(String(150), unique=True, nullable=False)
    Description = Column(String(500), nullable=True)
    IsActive = Column(Boolean, default=True)

    questions = relationship("Question", back_populates="category")


# ============================================================
# Questions
# ============================================================

# StatusID values
STATUS_OPEN = 1
STATUS_ANSWERED = 2
STATUS_CLOSED = 3

QUESTION_STATUS_LABELS = {
    STATUS_OPEN: "Open",
    STATUS_ANSWERED: "Answered",
    STATUS_CLOSED: "Closed",
}


class Question(Base):
    __tablename__ = "questions"

    QuestionID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    CategoryID = Column(Integer, ForeignKey("categories.CategoryID"), nullable=False)
    StatusID = Column(Integer, default=STATUS_OPEN)
    Title = Column(String(300), nullable=False)
    Description = Column(Text, nullable=False)
    AttachmentPath = Column(String(500), nullable=True)
    Source = Column(String(20), default="user")  # "user" | "ai_assistant"
    ViewsCount = Column(Integer, default=0)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="questions")
    category = relationship("Category", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


# ============================================================
# Answers
# ============================================================

class Answer(Base):
    __tablename__ = "answers"

    AnswerID = Column(Integer, primary_key=True, index=True)
    QuestionID = Column(Integer, ForeignKey("questions.QuestionID"), nullable=False)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    AnswerText = Column(Text, nullable=False)
    AttachmentPath = Column(String(500), nullable=True)
    IsAIGenerated = Column(Boolean, default=False)
    IsAccepted = Column(Boolean, default=False)
    Upvotes = Column(Integer, default=0)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    question = relationship("Question", back_populates="answers")
    user = relationship("User", back_populates="answers")
    comments = relationship("Comment", back_populates="answer", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="answer", cascade="all, delete-orphan")


# ============================================================
# Votes
# ============================================================

class Vote(Base):
    __tablename__ = "votes"

    VoteID = Column(Integer, primary_key=True, index=True)
    AnswerID = Column(Integer, ForeignKey("answers.AnswerID"), nullable=False)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    VoteType = Column(Integer, nullable=False)  # 1 = upvote, -1 = downvote

    answer = relationship("Answer", back_populates="votes")


# ============================================================
# Comments
# ============================================================

class Comment(Base):
    __tablename__ = "comments"

    CommentID = Column(Integer, primary_key=True, index=True)
    AnswerID = Column(Integer, ForeignKey("answers.AnswerID"), nullable=False)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    CommentText = Column(Text, nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)

    answer = relationship("Answer", back_populates="comments")


# ============================================================
# Gamification: Badges
# ============================================================

class Badge(Base):
    __tablename__ = "badges"

    BadgeID = Column(Integer, primary_key=True, index=True)
    Name = Column(String(100), unique=True, nullable=False)
    Description = Column(String(300), nullable=False)
    Icon = Column(String(50), default="FaMedal")
    PointsThreshold = Column(Integer, nullable=True)   # e.g. 100 points -> auto award
    Criteria = Column(String(300), nullable=True)      # human readable criteria


class UserBadge(Base):
    __tablename__ = "user_badges"

    UserBadgeID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    BadgeID = Column(Integer, ForeignKey("badges.BadgeID"), nullable=False)
    AwardedAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="badges")
    badge = relationship("Badge")


# ============================================================
# Notifications
# ============================================================

class Notification(Base):
    __tablename__ = "notifications"

    NotificationID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    Type = Column(String(50), default="general")
    Message = Column(String(500), nullable=False)
    Link = Column(String(300), nullable=True)
    IsRead = Column(Boolean, default=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)


# ============================================================
# Question views (one row per user per question, so the view counter
# reflects distinct viewers rather than page loads/refreshes/re-renders)
# ============================================================

class QuestionView(Base):
    __tablename__ = "question_views"
    __table_args__ = (
        UniqueConstraint("QuestionID", "UserID", name="uq_question_view_user"),
    )

    ViewID = Column(Integer, primary_key=True, index=True)
    QuestionID = Column(Integer, ForeignKey("questions.QuestionID"), nullable=False)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    ViewedAt = Column(DateTime, default=datetime.utcnow)


# ============================================================
# Monthly leaderboard. The main leaderboard shows only the CURRENT
# month's points (so it resets to zero every month); each month's final
# standings stay here permanently as browsable history. User.Points
# remains the all-time lifetime total (used for levels/badges, which
# are meant to be permanent achievements).
# ============================================================

class MonthlyPoints(Base):
    __tablename__ = "monthly_points"
    __table_args__ = (
        UniqueConstraint("UserID", "YearMonth", name="uq_monthly_points_user_month"),
    )

    MonthlyPointsID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    YearMonth = Column(String(7), nullable=False, index=True)  # "2026-09"
    Points = Column(Integer, default=0)


# ============================================================
# Password reset (forgot password with email verification)
# ============================================================

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    TokenID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    Code = Column(String(10), nullable=False)  # 6-digit verification code
    ExpiresAt = Column(DateTime, nullable=False)
    Used = Column(Boolean, default=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
