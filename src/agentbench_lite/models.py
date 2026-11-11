from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

class Agent(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: str = ""
    entrypoint: str
    version: str = "1.0.0"
    settings: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    capabilities: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now_utc)

class Evaluation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    suite_name: str
    status: str = "running"
    repeats: int = 1
    created_at: datetime = Field(default_factory=now_utc)
    finished_at: datetime | None = None
    error: str | None = None

class CaseResult(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    evaluation_id: str = Field(index=True)
    agent_id: str = Field(index=True)
    task_id: str
    repeat_index: int = 0
    status: str = "pending"
    input: str
    output: str = ""
    expected_output: str | None = None
    passed: bool = False
    score: float = 0.0
    latency_ms: float = 0.0
    error: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    tool_calls: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    evaluation_details: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    trace: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now_utc)
