"""
Gamification: points, levels, badge awarding, and the monthly leaderboard.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import User, Badge, MonthlyBadge, Notification, MonthlyPoints

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


def current_month_start() -> datetime:
    """Start of the current UTC month - the boundary for "did this
    happen this month" checks (first question/answer this month, 5
    accepted answers this month, etc.), used alongside current_year_month()
    wherever a badge's eligibility needs to be scoped to the same
    month its award gets recorded under."""
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)


def get_monthly_points_and_level(db: Session, user: User) -> tuple[int, str]:
    """The "Level" and points shown on a user's own profile/sidebar are
    meant to reset every month, same as the leaderboard - they reflect
    recent activity, not a permanent rank. (Badges are the permanent
    achievements; those are looked up separately and never reset.)
    Returns (points, level) for the CURRENT month only - 0/"Beginner"
    for anyone who hasn't done anything yet this month, regardless of
    their all-time total."""

    row = (
        db.query(MonthlyPoints)
        .filter(MonthlyPoints.UserID == user.UserID, MonthlyPoints.YearMonth == current_year_month())
        .first()
    )
    points = row.Points if row else 0
    return points, compute_level(points)


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
    # User.Points/Level still track a LIFETIME total in the background
    # (kept for potential future all-time reporting) but are no longer
    # shown anywhere in the product - the profile/sidebar/leaderboard
    # all show the monthly figures computed below instead.
    user.Points = (user.Points or 0) + points
    user.Level = compute_level(user.Points)
    db.add(user)

    old_monthly_points, old_monthly_level = get_monthly_points_and_level(db, user)
    _adjust_monthly_points(db, user, points)
    db.flush()
    new_monthly_points, new_monthly_level = get_monthly_points_and_level(db, user)
    leveled_up = new_monthly_level != old_monthly_level

    if leveled_up:
        db.add(Notification(
            UserID=user.UserID,
            Type="level_up",
            Message=f"Congratulations! You've reached the {new_monthly_level} level.",
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
    """Auto-award point-threshold badges the user newly qualifies for
    THIS MONTH. Checked against this month's points (not lifetime) -
    badges reset to none every month, same as points/level, so
    qualifying is re-evaluated fresh each month."""

    year_month = current_year_month()
    monthly_points, _ = get_monthly_points_and_level(db, user)

    already_earned_ids = {
        mb.BadgeID for mb in
        db.query(MonthlyBadge).filter(MonthlyBadge.UserID == user.UserID, MonthlyBadge.YearMonth == year_month).all()
    }

    eligible_badges = (
        db.query(Badge)
        .filter(Badge.PointsThreshold.isnot(None))
        .filter(Badge.PointsThreshold <= monthly_points)
        .all()
    )

    for badge in eligible_badges:
        if badge.BadgeID in already_earned_ids:
            continue
        db.add(MonthlyBadge(UserID=user.UserID, BadgeID=badge.BadgeID, YearMonth=year_month))
        db.add(Notification(
            UserID=user.UserID,
            Type="badge_earned",
            Message=f"You earned the \"{badge.Name}\" badge!",
        ))


def award_badge_manual(db: Session, user: User, badge_name: str):
    """Award a specific badge regardless of points (e.g. 'First Answer')
    for THIS MONTH. Scoped to the current month like everything else in
    this file - so e.g. "First Answer" means "first answer this month",
    not lifetime, and can be earned again next month. Idempotent within
    the same month (calling this twice in one month for an already-
    earned badge is a no-op), but a new month means a fresh chance to
    earn it, independent of whether it was earned in any past month."""

    badge = db.query(Badge).filter(Badge.Name == badge_name).first()
    if not badge:
        return

    year_month = current_year_month()
    exists = (
        db.query(MonthlyBadge)
        .filter(MonthlyBadge.UserID == user.UserID, MonthlyBadge.BadgeID == badge.BadgeID, MonthlyBadge.YearMonth == year_month)
        .first()
    )
    if exists:
        return

    db.add(MonthlyBadge(UserID=user.UserID, BadgeID=badge.BadgeID, YearMonth=year_month))
    db.add(Notification(
        UserID=user.UserID,
        Type="badge_earned",
        Message=f"You earned the \"{badge.Name}\" badge!",
    ))
