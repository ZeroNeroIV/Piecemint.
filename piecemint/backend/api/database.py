import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_DEFAULT_DB = "sqlite:///" + os.path.join(_ROOT, "piecemint.db")
DATABASE_URL = os.environ.get("PIECEMINT_DATABASE_URL", _DEFAULT_DB)


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_transaction_notes_column() -> None:
    """Add transactions.notes when the table predates the column (SQLite / Postgres)."""
    insp = inspect(engine)
    if not insp.has_table("transactions"):
        return
    cols = {c["name"] for c in insp.get_columns("transactions")}
    if "notes" in cols:
        return
    dialect = engine.dialect.name
    if dialect == "sqlite":
        ddl = "ALTER TABLE transactions ADD COLUMN notes TEXT NOT NULL DEFAULT ''"
    elif dialect == "postgresql":
        ddl = "ALTER TABLE transactions ADD COLUMN notes TEXT NOT NULL DEFAULT ''"
    else:
        ddl = "ALTER TABLE transactions ADD COLUMN notes TEXT NOT NULL DEFAULT ''"
    with engine.begin() as conn:
        conn.execute(text(ddl))


def init_db() -> None:
    from api import db_models  # noqa: F401 — register models

    Base.metadata.create_all(bind=engine)
    _ensure_transaction_notes_column()
