from __future__ import annotations
from datetime import datetime, timezone
from sqlmodel import Session, select
from .config import MAX_TASKS_PER_RUN
from .models import Agent, Evaluation, CaseResult
from .schemas import RunRequest
from .runner import execute_case
from .suites import load_suite

CORE_CAPABILITIES = {"text_input"}

def check_compatibility(session: Session, agent_ids: list[str], suite_name: str) -> dict:
    suite = load_suite(suite_name)
    required = set(suite.required_capabilities) | ({"document_input"} if suite.resources else set())
    report = []
    for agent_id in agent_ids:
        agent = session.get(Agent, agent_id)
        if agent is None:
            report.append({"agent_id": agent_id, "compatible": False, "missing_capabilities": [], "error": "Agent not found"})
            continue
        available = set(agent.capabilities or []) | CORE_CAPABILITIES
        missing = sorted(required - available)
        report.append({"agent_id": agent.id, "agent_name": agent.name, "compatible": not missing, "required_capabilities": sorted(required), "available_capabilities": sorted(available), "missing_capabilities": missing})
    return {"suite_name": suite_name, "compatible": all(x["compatible"] for x in report), "agents": report}

def create_evaluation(session: Session, request: RunRequest) -> Evaluation:
    agents = [session.get(Agent, agent_id) for agent_id in request.agent_ids]
    if any(agent is None for agent in agents): raise ValueError("One or more selected agents do not exist")
    suite = load_suite(request.suite_name)
    required = set(suite.required_capabilities) | (set(["document_input"]) if suite.resources else set())
    for agent in agents:
        missing = required - (set(agent.capabilities or []) | CORE_CAPABILITIES)
        if missing: raise ValueError(f"Agent '{agent.name}' is incompatible with suite '{request.suite_name}'. Missing capabilities: {', '.join(sorted(missing))}")
    if len(suite.tasks) * len(agents) * request.repeats > MAX_TASKS_PER_RUN: raise ValueError(f"Run exceeds configured limit of {MAX_TASKS_PER_RUN} case executions")
    resource_ids = {r.id for r in suite.resources}
    for task in suite.tasks:
        missing = set(task.resource_ids) - resource_ids
        if missing: raise ValueError(f"Task '{task.id}' references unknown resources: {', '.join(sorted(missing))}")
    evaluation = Evaluation(suite_name=request.suite_name, repeats=request.repeats, status="running")
    session.add(evaluation); session.commit(); session.refresh(evaluation)
    failures = 0
    try:
        for agent in agents:
            for repeat in range(request.repeats):
                for task in suite.tasks:
                    row = execute_case(agent, task, evaluation.id, repeat, suite.resources, {"suite_name": suite.name, "suite_version": suite.version})
                    failures += row.status in {"failed", "evaluation_failed"}
                    session.add(row)
        evaluation.status = "completed_with_errors" if failures else "completed"
    except Exception as exc:
        evaluation.status = "failed"; evaluation.error = str(exc); raise
    finally:
        evaluation.finished_at = datetime.now(timezone.utc)
        session.add(evaluation); session.commit(); session.refresh(evaluation)
    return evaluation

def evaluation_detail(session: Session, evaluation_id: str) -> dict:
    evaluation = session.get(Evaluation, evaluation_id)
    if evaluation is None: raise ValueError("Evaluation not found")
    rows = session.exec(select(CaseResult).where(CaseResult.evaluation_id == evaluation_id)).all()
    agents = {a.id: a for a in session.exec(select(Agent)).all()}
    summary = {}
    for row in rows:
        agent = agents.get(row.agent_id); key = row.agent_id
        item = summary.setdefault(key, {"agent_id": key, "agent_name": agent.name if agent else key, "version": agent.version if agent else "", "total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0, "avg_latency_ms": 0.0, "avg_score": 0.0, "total_tokens": 0})
        item["total"] += 1; item["passed"] += int(row.passed); item["failed"] += int(row.status in {"failed", "evaluation_failed"})
        item["avg_latency_ms"] += row.latency_ms; item["avg_score"] += row.score; item["total_tokens"] += int(row.usage.get("total_tokens", 0))
    for item in summary.values():
        n = item["total"] or 1; item["pass_rate"] = item["passed"] / n; item["avg_latency_ms"] /= n; item["avg_score"] /= n
    return {"evaluation": evaluation.model_dump(mode="json"), "summary": list(summary.values()), "results": [r.model_dump(mode="json") for r in rows]}
