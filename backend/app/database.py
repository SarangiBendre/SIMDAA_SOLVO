import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Load variables from .env
load_dotenv()


# Read database configuration
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_DRIVER = os.getenv("DB_DRIVER")
DB_TRUSTED_CONNECTION = os.getenv("DB_TRUSTED_CONNECTION")
DB_TRUST_SERVER_CERTIFICATE = os.getenv("DB_TRUST_SERVER_CERTIFICATE")


# Create ODBC connection string
connection_string = (
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"Trusted_Connection={DB_TRUSTED_CONNECTION};"
    f"TrustServerCertificate={DB_TRUST_SERVER_CERTIFICATE};"
)


# Encode the connection string for SQLAlchemy
connection_url = (
    "mssql+pyodbc:///?odbc_connect="
    + quote_plus(connection_string)
)


# Create database engine
engine = create_engine(
    connection_url,
    echo=True
)


# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for database models
Base = declarative_base()


# Database session dependency
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()