"""
Database configuration for SIMDAA SOLVO.

Defaults to a local SQLite file so the project runs anywhere with zero
external setup. Set DATABASE_URL in .env to point at SQL Server,
PostgreSQL, MySQL, etc. instead - no code changes required.

Examples:
  SQLite (default):
    DATABASE_URL=sqlite:///./simdaa_solvo.db

  SQL Server (matches the original project setup):
    DATABASE_URL=mssql+pyodbc://@YOUR_SERVER/SIMDAA_SOLVO?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes

  PostgreSQL:
    DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/simdaa_solvo
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./simdaa_solvo.db")

# Some providers (Render, Heroku, etc.) hand out connection strings
# starting with "postgres://", but SQLAlchemy 2.x requires the
# "postgresql://" scheme. Normalize it so pasting their URL in directly
# just works, instead of failing with a cryptic dialect error.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # Needed for SQLite when accessed from multiple threads (FastAPI default)
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
