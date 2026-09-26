"""
Seeds the database with the fixed reference data the app needs to be
usable immediately after first run: roles, an admin account, starter
categories, and the badge catalog.

Runs automatically on startup (see main.py) and is idempotent - safe
to call every time the app boots.
"""

import os
import logging
import secrets

from dotenv import load_dotenv

from app.database import SessionLocal
from app.models import Role, User, Category, Badge, ROLE_ADMIN, ROLE_MENTOR, ROLE_EMPLOYEE, ROLE_INTERN, ROLE_TRAINEE
from app.auth import hash_password

load_dotenv()
logger = logging.getLogger("simdaa.seed")

DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@simdaasolvo.local")

# System account that authors AI Assistant answers. Nobody logs in as
# this account - its password is a random value nobody knows.
AI_ASSISTANT_USERNAME = "ai_assistant"

ROLES = [
    (ROLE_ADMIN, "Admin"),
    (ROLE_MENTOR, "Mentor/Senior"),
    (ROLE_EMPLOYEE, "Employee"),
    (ROLE_INTERN, "Intern"),
    (ROLE_TRAINEE, "Trainee"),
]

CATEGORIES = [
    ("General", "Anything that doesn't fit a specific category yet."),
    ("Python Programming", "Python syntax, libraries, debugging, and best practices."),
    ("Data Analytics", "Data cleaning, EDA, pandas/NumPy, and analysis techniques."),
    ("Machine Learning", "Model building, training, evaluation, and ML algorithms."),
    ("Deep Learning & AI", "Neural networks, LLMs, computer vision, and NLP."),
    ("SQL & Databases", "Queries, schema design, and database concepts."),
    ("Statistics & Mathematics", "Probability, statistics, and the math behind ML."),
    ("Data Visualization", "Charts, dashboards, Matplotlib/Power BI/Tableau."),
    ("Tools & Environment", "Jupyter, Git, VS Code, environments, and setup issues."),
    ("Career & Onboarding", "Process, tooling, and getting-started questions."),
]

BADGES = [
    ("First Question", "Asked your first question.", "FaQuestionCircle", None),
    ("First Answer", "Posted your first answer.", "FaComments", None),
    ("Top Mentor", "Had 5 answers accepted.", "FaCrown", None),
    ("100 Points", "Earned 100 points on SIMDAA SOLVO.", "FaStar", 100),
    ("Helpful Contributor", "Earned 250 points helping others.", "FaHandsHelping", 250),
    ("Master Mentor", "Reached the Master Mentor level.", "FaMedal", 400),
]


def run_seed():
    db = SessionLocal()
    try:
        # ---------------- Roles ----------------
        for role_id, role_name in ROLES:
            if not db.query(Role).filter(Role.RoleID == role_id).first():
                db.add(Role(RoleID=role_id, RoleName=role_name))
        db.commit()

        # ---------------- Admin user ----------------
        if not db.query(User).filter(User.Username == DEFAULT_ADMIN_USERNAME).first():
            admin = User(
                RoleID=ROLE_ADMIN,
                Username=DEFAULT_ADMIN_USERNAME,
                PasswordHash=hash_password(DEFAULT_ADMIN_PASSWORD),
                FullName="System Administrator",
                Email=DEFAULT_ADMIN_EMAIL,
                Department="Administration",
                IsActive=True,
                Points=0,
                Level="Beginner",
            )
            db.add(admin)
            db.commit()
            logger.warning(
                "Seeded default admin user '%s'. CHANGE THIS PASSWORD after first login.",
                DEFAULT_ADMIN_USERNAME,
            )

        # ---------------- Categories ----------------
        for name, description in CATEGORIES:
            if not db.query(Category).filter(Category.CategoryName == name).first():
                db.add(Category(CategoryName=name, Description=description, IsActive=True))
        db.commit()

        # ---------------- AI Assistant system account ----------------
        if not db.query(User).filter(User.Username == AI_ASSISTANT_USERNAME).first():
            db.add(User(
                RoleID=ROLE_MENTOR,
                Username=AI_ASSISTANT_USERNAME,
                PasswordHash=hash_password(secrets.token_urlsafe(32)),
                FullName="AI Assistant",
                Email="ai-assistant@simdaasolvo.local",
                Department="System",
                IsActive=True,
                Points=0,
                Level="Beginner",
            ))
            db.commit()

        # ---------------- Badges ----------------
        for name, description, icon, threshold in BADGES:
            if not db.query(Badge).filter(Badge.Name == name).first():
                db.add(Badge(
                    Name=name,
                    Description=description,
                    Icon=icon,
                    PointsThreshold=threshold,
                ))
        db.commit()

    finally:
        db.close()
