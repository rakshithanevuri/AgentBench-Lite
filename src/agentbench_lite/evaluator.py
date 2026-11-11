from __future__ import annotations
import json
from typing import Any, Callable
from .schemas import TaskCase, EvaluationContext

CheckFunction = Callable[[TaskCase, str], bool]
ContextCheckFunction = Callable[[EvaluationContext], bool]
CHECK_REGISTRY: dict[str, CheckFunction] = {}
CONTEXT_CHECK_REGISTRY: dict[str, ContextCheckFunction] = {}

def register_check(name: str):
    def decorator(func: CheckFunction):
        if name in CHECK_REGISTRY or name in CONTEXT_CHECK_REGISTRY: raise ValueError(f"Check already registered: {name}")
        CHECK_REGISTRY[name] = func
        return func
    return decorator

def register_context_check(name: str):
    def decorator(func: ContextCheckFunction):
        if name in CHECK_REGISTRY or name in CONTEXT_CHECK_REGISTRY: raise ValueError(f"Check already registered: {name}")
        CONTEXT_CHECK_REGISTRY[name] = func
        return func
    return decorator

@register_check("not_empty")
def check_not_empty(task: TaskCase, output: str) -> bool: return bool(output.strip())
@register_check("exact_match")
def check_exact_match(task: TaskCase, output: str) -> bool: return task.expected_output is not None and output.strip() == task.expected_output.strip()
@register_check("contains")
def check_contains(task: TaskCase, output: str) -> bool: return task.expected_output is not None and task.expected_output.casefold() in output.casefold()
@register_check("starts_with")
def check_starts_with(task: TaskCase, output: str) -> bool: return task.expected_output is not None and output.casefold().startswith(task.expected_output.casefold())
@register_check("json_valid")
def check_json_valid(task: TaskCase, output: str) -> bool:
    try: json.loads(output); return True
    except (ValueError, TypeError): return False
@register_context_check("tool_called")
def check_tool_called(context: EvaluationContext) -> bool:
    expected = str(context.task.metadata.get("expected_tool", ""))
    return any(not expected or c.get("name") == expected for c in context.tool_calls)
@register_context_check("has_sources")
def check_has_sources(context: EvaluationContext) -> bool:
    return bool(context.metadata.get("sources") or context.metadata.get("source_count", 0))
@register_context_check("usage_reported")
def check_usage_reported(context: EvaluationContext) -> bool: return bool(context.usage)

def evaluate_context(context: EvaluationContext) -> tuple[bool, float, list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    for check in context.task.checks:
        try:
            if check in CONTEXT_CHECK_REGISTRY: passed = bool(CONTEXT_CHECK_REGISTRY[check](context))
            elif check in CHECK_REGISTRY: passed = bool(CHECK_REGISTRY[check](context.task, context.output))
            else: raise ValueError(f"Unknown evaluation check: {check}")
            reason = "Check passed" if passed else "Check did not pass"
            error = None
        except Exception as exc:
            passed, reason, error = False, "Evaluator raised an exception", f"{type(exc).__name__}: {exc}"
        results.append({"check": check, "passed": passed, "score": 1.0 if passed else 0.0, "weight": float(context.task.check_weights.get(check, 1.0)), "reason": reason, "error": error})
    total_weight = sum(max(0.0, x["weight"]) for x in results)
    score = (sum(x["score"] * max(0.0, x["weight"]) for x in results) / total_weight) if total_weight else 0.0
    passed = bool(results) and all(x["passed"] for x in results)
    return passed, round(score, 6), results

def evaluate_output(task: TaskCase, output: str) -> tuple[bool, float, list[dict[str, Any]]]:
    return evaluate_context(EvaluationContext(task=task, output=output))
