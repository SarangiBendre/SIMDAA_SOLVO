"""
Gamification: points, levels, badge awarding, and the monthly leaderboard.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import User, Badge, UserBadge, Notification, MonthlyPoints

# Point values
POINTS_ASK_QUESTION = 5
POINTS_ANSWER_QUESTION = 10
POINTS_ACCEPTED_ANSWER = 20
POINTS_UPVOTE_RECEIVED = 2

# Level thresholds, lowest to highest (based on lifetime points)
LEVELS = [
    (0, "Beginner"),
    (50, "Contributor"),
    (150, "Expert"),
    (400, "Master Mentor"),
]


def compute_level(points: int) -> str:
    level = LEVELS[0][1]
    for threshold, name in LEVELS:
        if points >= threshold:
            level = name
    return level


def current_year_month() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def _adjust_monthly_points(db: Session, user: User, delta: int):
    """Adds/subtracts delta from the CURRENT month's bucket only. Past
    months are frozen history and are never rewritten, even if content
    from that month is later deleted."""

    ym = current_year_month()
    row = (
        db.query(MonthlyPoints)
        .filter(MonthlyPoints.UserID == user.UserID, MonthlyPoints.YearMonth == ym)
        .first()
    )
    if not row:
        row = MonthlyPoints(UserID=user.UserID, YearMonth=ym, Points=0)
        db.add(row)
        db.flush()

    row.Points = max(0, (row.Points or 0) + delta)


def award_points(db: Session, user: User, points: int, reason: str = ""):
    user.Points = (user.Points or 0) + points
    new_level = compute_level(user.Points)

    leveled_up = new_level != user.Level
    user.Level = new_level

    db.add(user)
    _adjust_monthly_points(db, user, points)
    db.flush()

    if leveled_up:
        db.add(Notification(
            UserID=user.UserID,
            Type="level_up",
            Message=f"Congratulations! You've reached the {new_level} level.",
        ))

    _check_badges(db, user)
    return user


def deduct_points(db: Session, user: User, points: int, reason: str = ""):
    """Reverses points previously awarded (e.g. when the question/answer
    that earned them gets deleted). Lifetime points never go below 0.
    Badges already earned are NOT revoked - they're treated as permanent
    achievements, same as most gamification systems."""

    user.Points = max(0, (user.Points or 0) - points)
    user.Level = compute_level(user.Points)

    db.add(user)
    _adjust_monthly_points(db, user, -points)
    db.flush()

    return user


def _check_badges(db: Session, user: User):
    """Auto-award point-threshold badges the user newly qualifies for."""

    already_earned_ids = {
        ub.BadgeID for ub in
        db.query(UserBadge).filter(UserBadge.UserID == user.UserID).all()
    }

    eligible_badges = (
        db.query(Badge)
        .filter(Badge.PointsThreshold.isnot(None))
        .filter(Badge.PointsThreshold <= (user.Points or 0))
        .all()
    )

    for badge in eligible_badges:
        if badge.BadgeID in already_earned_ids:
            continue
        db.add(UserBadge(UserID=user.UserID, BadgeID=badge.BadgeID))
        db.add(Notification(
            UserID=user.UserID,
            Type="badge_earned",
            Message=f"You earned the \"{badge.Name}\" badge!",
        ))


def award_badge_manual(db: Session, user: User, badge_name: str):
    """Award a specific badge regardless of points (e.g. 'First Answer')."""

    badge = db.query(Badge).filter(Badge.Name == badge_name).first()
    if not badge:
        return

    exists = (
        db.query(UserBadge)
        .filter(UserBadge.UserID == user.UserID, UserBadge.BadgeID == badge.BadgeID)
        .first()
    )
    if exists:
        return

    db.add(UserBadge(UserID=user.UserID, BadgeID=badge.BadgeID))
    db.add(Notification(
        UserID=user.UserID,
        Type="badge_earned",
        Message=f"You earned the \"{badge.Name}\" badge!",
    ))
