from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Role, Question, Answer, Comment, Vote, Notification, UserBadge, QuestionView, ROLE_ADMIN
from app.auth import hash_password, get_current_user, require_role

router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    RoleID: int
    Username: str = Field(min_length=1)
    Password: str = Field(min_length=1)
    FullName: str = Field(min_length=1)
    Email: str = Field(min_length=1)
    Department: str = Field(min_length=1)


class UserUpdate(BaseModel):
    FullName: str | None = None
    Email: str | None = None
    Department: str | None = None
    RoleID: int | None = None


def _serialize(user: User):
    return {
        "UserID": user.UserID,
        "RoleID": user.RoleID,
        "RoleName": user.role.RoleName if user.role else None,
        "Username": user.Username,
        "FullName": user.FullName,
        "Email": user.Email,
        "Department": user.Department,
        "IsActive": user.IsActive,
        "Points": user.Points,
        "Level": user.Level,
        "CreatedAt": user.CreatedAt,
        "UpdatedAt": user.UpdatedAt,
        "LastLogin": user.LastLogin,
    }


@router.get("/")
def get_users(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.FullName).all()
    return [_serialize(u) for u in users]


@router.post("/")
def create_user(user: UserCreate, current_user=Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    if db.query(User).filter(User.Username == user.Username).first():
        raise HTTPException(status_code=409, detail="Username already exists")

    if db.query(User).filter(User.Email == user.Email).first():
        raise HTTPException(status_code=409, detail="Email already exists")

    if not db.query(Role).filter(Role.RoleID == user.RoleID).first():
        raise HTTPException(status_code=400, detail="Invalid RoleID")

    new_user = User(
        RoleID=user.RoleID,
        Username=user.Username,
        PasswordHash=hash_password(user.Password),
        FullName=user.FullName,
        Email=user.Email,
        Department=user.Department,
        IsActive=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", **_serialize(new_user)}


@router.get("/profile/{user_id}")
def get_user_profile(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    questions_count = len(user.questions)
    answers_count = len(user.answers)
    accepted_answers = sum(1 for a in user.answers if a.IsAccepted)

    return {
        **_serialize(user),
        "QuestionsAsked": questions_count,
        "AnswersPosted": answers_count,
        "AcceptedAnswers": accepted_answers,
        "Badges": [
            {
                "BadgeID": ub.badge.BadgeID,
                "Name": ub.badge.Name,
                "Description": ub.badge.Description,
                "Icon": ub.badge.Icon,
                "AwardedAt": ub.AwardedAt,
            }
            for ub in user.badges
        ],
    }


@router.get("/{user_id}")
def get_user(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize(user)


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    is_self = current_user["UserID"] == user_id
    is_admin = current_user.get("RoleID") == ROLE_ADMIN
    if not (is_self or is_admin):
        raise HTTPException(status_code=403, detail="You can only update your own profile")

    user = db.query(User).filter(User.UserID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.FullName is not None:
        user.FullName = payload.FullName
    if payload.Email is not None:
        user.Email = payload.Email
    if payload.Department is not None:
        user.Department = payload.Department
    if payload.RoleID is not None and is_admin:
        user.RoleID = payload.RoleID

    db.commit()
    return {"message": "User updated successfully"}


@router.delete("/{user_id}")
def delete_user(user_id: int, current_user=Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.IsActive = False
    db.commit()
    return {"message": "User deactivated successfully"}


@router.put("/{user_id}/reactivate")
def reactivate_user(user_id: int, current_user=Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.IsActive = True
    db.commit()
    return {"message": "User reactivated successfully"}


@router.delete("/{user_id}/permanent")
def delete_user_permanently(user_id: int, current_user=Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    """Hard-deletes a user and everything tied to them: their own
    questions (and, as a consequence, all answers/comments/votes on
    those questions - including ones from other people), their answers
    on other people's questions, their comments, votes, notifications,
    badges, and view history. This cannot be undone - Deactivate is the
    reversible alternative and should be preferred unless the account
    truly needs to be erased."""

    user = db.query(User).filter(User.UserID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == current_user["UserID"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    # Their own questions: delete via ORM objects so cascade="all,
    # delete-orphan" on Question.answers / Answer.comments / Answer.votes
    # takes care of everything hanging off each question, even answers
    # posted by other people.
    own_questions = db.query(Question).filter(Question.UserID == user_id).all()
    for q in own_questions:
        db.delete(q)

    # Their own answers left on OTHER people's questions aren't reached
    # by the cascade above, so clean those up (and anything hanging off
    # them) explicitly.
    own_answers = db.query(Answer).filter(Answer.UserID == user_id).all()
    for a in own_answers:
        db.delete(a)

    db.query(Comment).filter(Comment.UserID == user_id).delete()
    db.query(Vote).filter(Vote.UserID == user_id).delete()
    db.query(Notification).filter(Notification.UserID == user_id).delete()
    db.query(UserBadge).filter(UserBadge.UserID == user_id).delete()
    db.query(QuestionView).filter(QuestionView.UserID == user_id).delete()

    db.delete(user)
    db.commit()

    return {"message": "User permanently deleted"}
