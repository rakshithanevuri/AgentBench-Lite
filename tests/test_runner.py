from agentbench_lite.agents import get_agent
from agentbench_lite.models import Agent
from agentbench_lite.runner import execute_case
from agentbench_lite.schemas import TaskCase

def test_starter_agent_executes_without_network():
    agent = Agent(id="agent-1", name="starter", entrypoint="demo_starter_agent")
    task = TaskCase(id="capital", input="What is the capital of France?", expected_output="Paris", checks=["exact_match"])
    result = execute_case(agent, task, "eval-1")
    assert result.status == "completed"
    assert result.output == "Paris"
    assert result.passed is True
    assert result.latency_ms >= 0
    assert result.trace

def test_unknown_agent_is_recorded_as_failed_case():
    agent = Agent(id="agent-1", name="bad", entrypoint="does_not_exist")
    task = TaskCase(id="case-1", input="hello")
    result = execute_case(agent, task, "eval-1")
    assert result.status == "failed"
    assert result.passed is False
    assert "Unknown agent entrypoint" in (result.error or "")
def test_http_agent_executes_with_mocked_response(monkeypatch):
    from types import SimpleNamespace
    from agentbench_lite import agents

    def fake_post(*args, **kwargs):
        assert args[0] == "http://127.0.0.1:9000/agent"
        assert kwargs["json"]["input"] == "What is the capital of France?"
        assert kwargs["json"]["protocol_version"] == "1.0"
        return SimpleNamespace(
            json=lambda: {"output": "Paris"},
            raise_for_status=lambda: None,
        )

    monkeypatch.setattr(agents.httpx, "post", fake_post)

    agent = Agent(
        id="agent-http",
        name="HTTP Test Agent",
        entrypoint="http_agent",
        settings={"endpoint": "http://127.0.0.1:9000/agent"},
    )

    task = TaskCase(
        id="capital",
        input="What is the capital of France?",
        expected_output="Paris",
        checks=["exact_match"],
    )

    result = execute_case(agent, task, "eval-http")

    assert result.status == "completed"
    assert result.output == "Paris"
    assert result.passed is True

def test_runner_passes_tool_calls_and_metadata_to_evaluator(monkeypatch):
    from agentbench_lite import runner
    from agentbench_lite.evaluator import register_context_check
    from agentbench_lite.schemas import AgentOutput

    @register_context_check("runner_context_test")
    def check_agent_context(context):
        has_search = any(
            call.get("name") == "search"
            for call in context.tool_calls
        )
        has_sources = context.metadata.get("source_count", 0) > 0
        return has_search and has_sources

    def fake_agent(task_input, settings):
        return AgentOutput(
            output="Found the answer",
            tool_calls=[{"name": "search"}],
            metadata={"source_count": 2},
        )

    monkeypatch.setattr(runner, "get_agent", lambda name: fake_agent)

    agent = Agent(
        id="agent-context",
        name="Context Test Agent",
        entrypoint="fake_agent",
    )

    task = TaskCase(
        id="context-test",
        input="Find information",
        checks=["runner_context_test"],
    )

    result = runner.execute_case(agent, task, "eval-context")

    assert result.status == "completed"
    assert result.passed is True
    assert result.score == 1.0
    assert result.tool_calls == [{"name": "search"}]

def test_runner_transfers_benchmark_resources_to_http_protocol(monkeypatch):
    from types import SimpleNamespace
    from agentbench_lite import agents
    from agentbench_lite.schemas import BenchmarkResource
    seen = {}
    def fake_post(url, **kwargs):
        seen.update(kwargs["json"])
        return SimpleNamespace(json=lambda: {"output": "The file says blue", "metadata": {"source_count": 1}}, raise_for_status=lambda: None)
    monkeypatch.setattr(agents.httpx, "post", fake_post)
    agent = Agent(id="resource-agent", name="resource", entrypoint="http_agent", settings={"endpoint":"http://127.0.0.1:9000/agent"}, capabilities=["document_input"])
    task = TaskCase(id="doc-q", input="What colour?", checks=["not_empty"], resource_ids=["doc-1"])
    resource = BenchmarkResource(id="doc-1", name="sample.txt", content="The colour is blue.")
    result = execute_case(agent, task, "eval-resource", resources=[resource])
    assert result.status == "completed"
    assert seen["protocol_version"] == "1.0"
    assert seen["resources"][0]["content"] == "The colour is blue."
    assert seen["task_id"] == "doc-q"
