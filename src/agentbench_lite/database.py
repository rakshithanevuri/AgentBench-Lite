from sqlalchemy import inspect, text
from sqlmodel import SQLModel, Session, create_engine
from .config import DATABASE_URL

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    # Safe additive migration for databases created by AgentBench Lite 0.1.
    if DATABASE_URL.startswith("sqlite"):
        inspector = inspect(engine)
        if "agent" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("agent")}
            if "capabilities" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE agent ADD COLUMN capabilities JSON NOT NULL DEFAULT '[]'"))
        if "caseresult" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("caseresult")}
            with engine.begin() as conn:
                if "metadata_json" not in cols:
                    conn.execute(text("ALTER TABLE caseresult ADD COLUMN metadata_json JSON NOT NULL DEFAULT '{}'"))
                if "evaluation_details" not in cols:
                    conn.execute(text("ALTER TABLE caseresult ADD COLUMN evaluation_details JSON NOT NULL DEFAULT '[]'"))

def get_session():
    with Session(engine) as session:
        yield session
