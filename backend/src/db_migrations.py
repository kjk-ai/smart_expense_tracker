from sqlalchemy import text

from .database import engine
from . import models

def ensure_schema() -> None:
    _ensure_user_columns()
    _ensure_tables()

def _ensure_user_columns() -> None:
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(users)"))
        existing = {row[1] for row in result.fetchall()}

        if "country_code" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN country_code VARCHAR"))
            conn.execute(text("UPDATE users SET country_code='US' WHERE country_code IS NULL"))
        if "timezone" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN timezone VARCHAR"))
            conn.execute(text("UPDATE users SET timezone='UTC' WHERE timezone IS NULL"))
        if "culture_tags" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN culture_tags TEXT"))
            conn.execute(text("UPDATE users SET culture_tags='[]' WHERE culture_tags IS NULL"))
        if "calendar_opt_in" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN calendar_opt_in BOOLEAN"))
            conn.execute(text("UPDATE users SET calendar_opt_in=1 WHERE calendar_opt_in IS NULL"))

def _ensure_tables() -> None:
    models.HolidayEvent.__table__.create(bind=engine, checkfirst=True)
    models.HolidayInsight.__table__.create(bind=engine, checkfirst=True)

    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(holiday_insights)"))
        existing = {row[1] for row in result.fetchall()}
        if "status" not in existing:
            conn.execute(text("ALTER TABLE holiday_insights ADD COLUMN status VARCHAR"))
            conn.execute(text("UPDATE holiday_insights SET status='ok' WHERE status IS NULL"))
