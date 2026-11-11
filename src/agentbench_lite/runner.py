from __future__ import annotations
import time
from typing import Any
from .agents import get_agent
from .evaluator import evaluate_context
from .models import Agent, CaseResult
from .schemas import TaskCase, AgentOutput, EvaluationContext, BenchmarkResource

def execute_case(agent: Agent, task: TaskCase, evaluation_id: str, repeat_index: int = 0, resources: list[BenchmarkResource] | None = None, suite_context: dict[str, Any] | None = None) -> CaseResult:
    started = time.perf_counter()
    trace: list[dict[str, Any]] = [{"event": "agent.started", "task_id": task.id, "protocol_version": "1.0"}]
    raw_result: AgentOutput | None = None
    try:
        fn = get_agent(agent.entrypoint)
        settings = dict(agent.settings or {})
        selected_resources = [r.model_dump(mode="json") for r in (resources or []) if not task.resource_ids or r.id in task.resource_ids]
        settings["_invocation"] = {"task_id": task.id, "context": {**(suite_context or {}), "task_metadata": task.metadata}, "resources": selected_resources, "metadata": {"tags": task.tags}}
        raw = fn(task.input, settings)
        raw_result = raw if isinstance(raw, AgentOutput) else AgentOutput.model_validate(raw) if isinstance(raw, dict) else AgentOutput(output=str(raw))
        trace.append({"event": "agent.completed", "tool_call_count": len(raw_result.tool_calls)})
        context = EvaluationContext(task=task, output=raw_result.output, tool_calls=raw_result.tool_calls, usage=raw_result.usage, metadata=raw_result.metadata)
        try:
            passed, score, checks = evaluate_context(context)
            evaluator_errors = [item for item in checks if item.get("error")]
            if evaluator_errors:
                status, error = "evaluation_failed", "; ".join(item["error"] for item in evaluator_errors)
                trace.append({"event": "evaluation.failed", "checks": checks})
            else:
                status, error = "completed", None
                trace.append({"event": "evaluation.completed", "checks": checks})
        except Exception as exc:
            passed, score, checks = False, 0.0, []
            status, error = "evaluation_failed", f"{type(exc).__name__}: {exc}"
            trace.append({"event": "evaluation.failed", "error_type": type(exc).__name__})
        latency = (time.perf_counter() - started) * 1000
        return CaseResult(evaluation_id=evaluation_id, agent_id=agent.id, task_id=task.id, repeat_index=repeat_index, status=status, input=task.input, output=raw_result.output, expected_output=task.expected_output, passed=passed, score=score, latency_ms=latency, error=error, usage=raw_result.usage, tool_calls=raw_result.tool_calls, metadata_json=raw_result.metadata, evaluation_details=checks, trace=trace)
    except Exception as exc:
        latency = (time.perf_counter() - started) * 1000
        trace.append({"event": "agent.failed", "error_type": type(exc).__name__})
        return CaseResult(evaluation_id=evaluation_id, agent_id=agent.id, task_id=task.id, repeat_index=repeat_index, status="failed", input=task.input, output="", expected_output=task.expected_output, passed=False, score=0.0, latency_ms=latency, error=f"{type(exc).__name__}: {exc}", trace=trace)
