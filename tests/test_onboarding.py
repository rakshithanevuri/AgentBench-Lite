from agentbench_lite.agents import _local_endpoint, discover_http_agent
import pytest


def test_local_endpoint_accepts_loopback():
    base, path = _local_endpoint('http://127.0.0.1:9001/agent')
    assert base == 'http://127.0.0.1:9001'
    assert path == '/agent'


def test_local_endpoint_rejects_public_host():
    with pytest.raises(ValueError, match='localhost/loopback'):
        _local_endpoint('https://example.com/agent')


def test_discovery_reads_health_and_manifest(monkeypatch):
    class Response:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload
            self.is_success = 200 <= status_code < 300
        def json(self):
            return self._payload

    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, url):
            if url.endswith('/health'):
                return Response(200, {'status': 'ok'})
            return Response(200, {'protocol_version': '1.0', 'capabilities': ['text_input', 'document_input']})

    monkeypatch.setattr('agentbench_lite.agents.httpx.Client', Client)
    result = discover_http_agent('http://127.0.0.1:9001/agent')
    assert result['reachable'] is True
    assert result['manifest_found'] is True
    assert result['capabilities'] == ['document_input', 'text_input']
