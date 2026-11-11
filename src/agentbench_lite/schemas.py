from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = ""
    entrypoint: str = Field(description="Registered Python agent adapter")
    version: str = "1.0.0"
    settings: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)

class AgentUpdate(BaseModel):
    description: str | None = None
    version: str | None = None
    settings: dict[str, Any] | None = None
    capabilities: list[str] | None = None

class BenchmarkResource(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    name: str
    mime_type: str = "text/plain"
    content: str | None = None
    content_base64: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content", "content_base64")
    @classmethod
    def limit_resource_size(cls, value):
        if value is not None and len(value) > 5_000_000:
            raise ValueError("A benchmark resource cannot exceed 5 MB of encoded/text content")
        return value

class TaskCase(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    input: str
    expected_output: str | None = None
    checks: list[str] = Field(default_factory=lambda: ["not_empty"])
    check_weights: dict[str, float] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    resource_ids: list[str] = Field(default_factory=list)

class TaskSuite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    description: str = ""
    version: str = "1.0"
    required_capabilities: list[str] = Field(default_factory=list)
    resources: list[BenchmarkResource] = Field(default_factory=list)
    tasks: list[TaskCase] = Field(min_length=1)

class RunRequest(BaseModel):
    agent_ids: list[str] = Field(min_length=1, max_length=10)
    suite_name: str
    repeats: int = Field(default=1, ge=1, le=5)

class AgentOutput(BaseModel):
    output: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, int | float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class AgentInvocation(BaseModel):
    protocol_version: str = "1.0"
    task_id: str
    input: str
    context: dict[str, Any] = Field(default_factory=dict)
    resources: list[BenchmarkResource] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvaluationContext(BaseModel):
    task: TaskCase
    output: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, int | float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
