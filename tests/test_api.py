from fastapi.testclient import TestClient
from agentbench_lite.api import app

def test_health_and_registry():
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        registry = client.get("/api/agents/registry").json()["entrypoints"]
        assert "demo_starter_agent" in registry

def test_protocol_and_suite_endpoints():
    with TestClient(app) as client:
        protocol = client.get("/api/protocol").json()
        assert protocol["protocol_version"] == "1.0"
        assert "resources" in protocol["optional_request_fields"]
        assert any(s["name"] == "starter" for s in client.get("/api/suites").json())
