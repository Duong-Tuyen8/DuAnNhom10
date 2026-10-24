from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./club_management.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Lightweight migration for existing SQLite databases.
# `Base.metadata.create_all()` only creates missing tables, it never adds new
# columns to a table that already exists. Because the `users` table gained the
# social-login columns, `members` gained profile columns, and `attendances`
# gained proof / verification columns,
# we patch old databases in place so the app keeps working without data loss.
# ---------------------------------------------------------------------------
_ADDED_COLUMNS = {
    "users": {
        "email": "VARCHAR",
        "full_name": "VARCHAR",
        "auth_provider": "VARCHAR DEFAULT 'local'",
        "provider_user_id": "VARCHAR",
    },
    "members": {
        "date_of_birth": "DATE",
        "gender": "VARCHAR",
        "class_name": "VARCHAR",
        "department": "VARCHAR",
    },
    "attendances": {
        "checked_in_at": "DATETIME",
        "proof_image_url": "VARCHAR",
        "verified_by": "INTEGER",
        "verified_at": "DATETIME",
        "reject_reason": "TEXT DEFAULT ''",
    },
}


def ensure_schema() -> None:
    """Create missing tables and add missing columns (safe to run repeatedly)."""
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in _ADDED_COLUMNS.items():
            if table not in existing_tables:
                continue
            current = {col["name"] for col in inspector.get_columns(table)}
            for column, ddl in columns.items():
                if column not in current:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
