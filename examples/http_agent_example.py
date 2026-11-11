"""Minimal generic AgentBench Lite protocol-v1 HTTP agent.

Run from the project root after installing dependencies:
    uvicorn examples.http_agent_example:app --host 127.0.0.1 --port 9001
Register http_agent at http://127.0.0.1:9001/agent.
"""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any

app = FastAPI(title="Example external agent")

class Invocation(BaseModel):
    protocol_version: str = "1.0"
    task_id: str = ""
    input: str
    context: dict[str, Any] = Field(default_factory=dict)
    resources: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

@app.get("/health")
def health():
    return {"status": "ok", "agent": "example-http-agent"}

@app.get("/manifest")
def manifest():
    # Capabilities are claims by the agent developer; benchmark compatibility
    # is still checked by AgentBench before a run.
    return {
        "protocol_version": "1.0",
        "name": "Example HTTP Agent",
        "capabilities": ["text_input", "document_input", "usage_reporting"],
        "input": {"modalities": ["text"], "resources": ["text/plain"]},
        "response": {"required": ["output"], "optional": ["tool_calls", "usage", "metadata"]},
    }

@app.post("/agent")
def invoke(request: Invocation):
    # Replace this deterministic example with your own framework/model pipeline.
    resource_text = "\n".join(str(r.get("content", "")) for r in request.resources)
    question = request.input.casefold()
    if "capital of france" in question:
        answer = "Paris"
    elif "6 multiplied by 7" in question or "6 times 7" in question:
        answer = "42"
    elif "annual leave" in question and "20 days" in resource_text.casefold():
        answer = "20 days"
    elif resource_text:
        answer = f"Received {len(request.resources)} benchmark resource(s)."
    else:
        answer = "I don't know."
    return {
        "output": answer,
        "tool_calls": [],
        "usage": {},
        "metadata": {"resource_count": len(request.resources)},
    }
