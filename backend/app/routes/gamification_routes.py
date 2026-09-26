from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Badge, UserBadge, MonthlyPoints
from app.auth import get_current_user
from app.Services import gamification_service as gamify

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get("/leaderboard")
def leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """Current month's leaderboard - resets to zero at the start of each
    month. Use /leaderboard/history to see past months."""

    ym = gamify.current_year_month()

    rows = (
        db.query(MonthlyPoints, User)
        .join(User, User.UserID == MonthlyPoints.UserID)
        .filter(MonthlyPoints.YearMonth == ym, User.IsActive.is_(True), MonthlyPoints.Points > 0)
        .order_by(MonthlyPoints.Points.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "UserID": u.UserID,
            "FullName": u.FullName,
            "Department": u.Department,
            "Points": mp.Points,
            "Level": u.Level,
            "BadgeCount": len(u.badges),
        }
        for mp, u in rows
    ]


@router.get("/leaderboard/months")
def leaderboard_months(db: Session = Depends(get_db)):
    """Every YearMonth that has recorded data, newest first - for a
    month-picker on the leaderboard history view."""

    months = (
        db.query(MonthlyPoints.YearMonth)
        .distinct()
        .order_by(MonthlyPoints.YearMonth.desc())
        .all()
    )
    return [m[0] for m in months]


@router.get("/leaderboard/history")
def leaderboard_history(month: str, limit: int = 20, db: Session = Depends(get_db)):
    """Frozen standings for a past month, e.g. ?month=2026-08. Once a
    month ends its numbers don't change, even if points are later
    adjusted (deletions only ever touch the CURRENT month's bucket)."""

    rows = (
        db.query(MonthlyPoints, User)
        .join(User, User.UserID == MonthlyPoints.UserID)
        .filter(MonthlyPoints.YearMonth == month, MonthlyPoints.Points > 0)
        .order_by(MonthlyPoints.Points.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "UserID": u.UserID,
            "FullName": u.FullName,
            "Department": u.Department,
            "Points": mp.Points,
            "Level": u.Level,
        }
        for mp, u in rows
    ]


@router.get("/badges")
def all_badges(db: Session = Depends(get_db)):
    badges = db.query(Badge).all()
    return [
        {
            "BadgeID": b.BadgeID,
            "Name": b.Name,
            "Description": b.Description,
            "Icon": b.Icon,
            "Criteria": b.Criteria or (f"{b.PointsThreshold} points" if b.PointsThreshold else "Special achievement"),
        }
        for b in badges
    ]


@router.get("/my-badges")
def my_badges(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    earned = db.query(UserBadge).filter(UserBadge.UserID == current_user["UserID"]).all()
    return [
        {
            "BadgeID": ub.badge.BadgeID,
            "Name": ub.badge.Name,
            "Description": ub.badge.Description,
            "Icon": ub.badge.Icon,
            "AwardedAt": ub.AwardedAt,
        }
        for ub in earned
    ]


@router.get("/levels")
def levels():
    return [{"MinPoints": threshold, "Level": name} for threshold, name in gamify.LEVELS]
