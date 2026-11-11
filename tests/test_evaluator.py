from agentbench_lite.evaluator import evaluate_output
from agentbench_lite.schemas import TaskCase

def test_exact_match_and_not_empty_pass():
    task = TaskCase(id="a", input="q", expected_output="Paris", checks=["exact_match", "not_empty"])
    passed, score, checks = evaluate_output(task, "Paris")
    assert passed is True
    assert score == 1.0
    assert all(item["passed"] for item in checks)

def test_contains_is_case_insensitive():
    task = TaskCase(id="a", input="q", expected_output="paris", checks=["contains"])
    assert evaluate_output(task, "The answer is PARIS.")[0] is True

def test_missing_expected_answer_does_not_pass_exact_match():
    task = TaskCase(id="a", input="q", checks=["exact_match"])
    passed, score, _ = evaluate_output(task, "anything")
    assert passed is False and score == 0.0

def test_custom_check_can_be_registered():
    from agentbench_lite.evaluator import register_check

    @register_check("test_starts_with")
    def starts_with(task, output):
        return output.startswith(task.expected_output)

    task = TaskCase(
        id="custom",
        input="Say hello",
        expected_output="Hello",
        checks=["test_starts_with"],
    )

    passed, score, checks = evaluate_output(task, "Hello there!")

    assert passed is True
    assert score == 1.0
    assert checks[0]["check"] == "test_starts_with"

def test_context_check_can_inspect_tool_calls():
    from agentbench_lite.evaluator import (
        register_context_check,
        evaluate_context,
    )
    from agentbench_lite.schemas import EvaluationContext

    @register_context_check("uses_search_tool")
    def uses_search(context):
        return any(
            call.get("name") == "search"
            for call in context.tool_calls
        )

    task = TaskCase(
        id="tool-test",
        input="Find information",
        checks=["uses_search_tool"],
    )

    context = EvaluationContext(
        task=task,
        output="Found the answer",
        tool_calls=[{"name": "search"}],
    )

    passed, score, checks = evaluate_context(context)

    assert passed is True
    assert score == 1.0
    assert checks[0]["check"] == "uses_search_tool"

def test_weighted_checks_return_diagnostics():
    task = TaskCase(id="weighted", input="q", expected_output="Paris", checks=["exact_match", "not_empty"], check_weights={"exact_match": 3, "not_empty": 1})
    passed, score, details = evaluate_output(task, "Paris")
    assert passed and score == 1.0
    assert details[0]["weight"] == 3
    assert details[0]["reason"] == "Check passed"

def test_json_valid_check():
    task = TaskCase(id="json", input="return json", checks=["json_valid"])
    assert evaluate_output(task, '{"ok": true}')[0]
    assert not evaluate_output(task, "not json")[0]
