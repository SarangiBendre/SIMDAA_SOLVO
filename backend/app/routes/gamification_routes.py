from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Badge, MonthlyBadge, MonthlyPoints
from app.auth import get_current_user
from app.Services import gamification_service as gamify

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get("/leaderboard")
def leaderboard(limit: int = 10, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
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

    badge_counts = dict(
        db.query(MonthlyBadge.UserID, func.count(MonthlyBadge.MonthlyBadgeID))
        .filter(MonthlyBadge.YearMonth == ym)
        .group_by(MonthlyBadge.UserID)
        .all()
    )

    return [
        {
            "UserID": u.UserID,
            "FullName": u.FullName,
            "Department": u.Department,
            "Points": mp.Points,
            # Level is derived from THIS month's points, not the lifetime
            # User.Level column - everything on this page is monthly now,
            # so the level shown next to it has to match the same basis.
            "Level": gamify.compute_level(mp.Points),
            "BadgeCount": badge_counts.get(u.UserID, 0),
        }
        for mp, u in rows
    ]


@router.get("/leaderboard/months")
def leaderboard_months(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
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
def leaderboard_history(month: str, limit: int = 20, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
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

    badge_counts = dict(
        db.query(MonthlyBadge.UserID, func.count(MonthlyBadge.MonthlyBadgeID))
        .filter(MonthlyBadge.YearMonth == month)
        .group_by(MonthlyBadge.UserID)
        .all()
    )

    return [
        {
            "UserID": u.UserID,
            "FullName": u.FullName,
            "Department": u.Department,
            "Points": mp.Points,
            "Level": gamify.compute_level(mp.Points),
            "BadgeCount": badge_counts.get(u.UserID, 0),
        }
        for mp, u in rows
    ]


@router.get("/badges")
def all_badges(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
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
    """This month's badges only - badges reset to none at the start of
    each month, same as points/level. See /my-badges/history for past
    months."""
    ym = gamify.current_year_month()
    earned = (
        db.query(MonthlyBadge)
        .filter(MonthlyBadge.UserID == current_user["UserID"], MonthlyBadge.YearMonth == ym)
        .all()
    )
    return [
        {
            "BadgeID": mb.badge.BadgeID,
            "Name": mb.badge.Name,
            "Description": mb.badge.Description,
            "Icon": mb.badge.Icon,
            "AwardedAt": mb.AwardedAt,
        }
        for mb in earned
    ]


@router.get("/my-badges/history")
def my_badges_history(month: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Which badges were earned in a specific past month, e.g.
    ?month=2026-09 - for the same month-picker used on the leaderboard,
    so badge history can be reviewed per month alongside points."""
    earned = (
        db.query(MonthlyBadge)
        .filter(MonthlyBadge.UserID == current_user["UserID"], MonthlyBadge.YearMonth == month)
        .all()
    )
    return [
        {
            "BadgeID": mb.badge.BadgeID,
            "Name": mb.badge.Name,
            "Description": mb.badge.Description,
            "Icon": mb.badge.Icon,
            "AwardedAt": mb.AwardedAt,
        }
        for mb in earned
    ]


@router.get("/levels")
def levels(current_user=Depends(get_current_user)):
    return [{"MinPoints": threshold, "Level": name} for threshold, name in gamify.LEVELS]
