from __future__ import annotations
import ipaddress
from urllib.parse import urlunparse
from urllib.parse import urlparse
import httpx
from collections.abc import Callable
from typing import Any
from .schemas import AgentOutput, AgentInvocation

AgentFunction = Callable[[str, dict[str, Any]], str | dict[str, Any] | AgentOutput]
REGISTRY: dict[str, AgentFunction] = {}

def register_agent(name: str):
    """Register a local Python adapter using the stable (input, settings) signature."""
    def decorator(fn: AgentFunction):
        if name in REGISTRY:
            raise ValueError(f"Agent entrypoint already registered: {name}")
        REGISTRY[name] = fn
        return fn
    return decorator

def get_agent(name: str) -> AgentFunction:
    try:
        return REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown agent entrypoint '{name}'. Registered: {', '.join(sorted(REGISTRY))}") from exc

@register_agent("demo_echo")
def demo_echo(task_input: str, settings: dict[str, Any]) -> str:
    return f"{settings.get('prefix', '')}{task_input}".strip()

@register_agent("demo_keyword_agent")
def demo_keyword_agent(task_input: str, settings: dict[str, Any]) -> str:
    for key, value in settings.get("responses", {}).items():
        if key.lower() in task_input.lower(): return str(value)
    return str(settings.get("fallback", "I don't know."))

@register_agent("demo_starter_agent")
def demo_starter_agent(task_input: str, settings: dict[str, Any]) -> str:
    text = task_input.casefold()
    if "capital of france" in text: return "Paris"
    if "6 multiplied by 7" in text or "6 times 7" in text: return "42"
    return str(settings.get("fallback", "I don't know."))

@register_agent("http_agent")
def http_agent(task_input: str, settings: dict[str, Any]) -> str | dict[str, Any]:
    """Invoke a local HTTP agent using protocol v1; legacy input-only agents remain compatible."""
    endpoint = str(settings.get("endpoint", "")).strip()
    if not endpoint: raise ValueError("HTTP agent endpoint is required")
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Invalid HTTP agent endpoint")
    hostname = parsed.hostname.lower()
    try: is_loopback = ipaddress.ip_address(hostname).is_loopback
    except ValueError: is_loopback = hostname == "localhost"
    if not is_loopback: raise ValueError("Only localhost and loopback endpoints are supported in this release")
    timeout = float(settings.get("timeout", 10))
    if not 0.1 <= timeout <= 120: raise ValueError("Timeout must be between 0.1 and 120 seconds")
    # Extra fields are supplied by runner via per-call settings; old adapters ignore them.
    invocation = settings.get("_invocation", {})
    payload = {"protocol_version": "1.0", "input": task_input, **invocation}
    headers = {"Content-Type": "application/json"}
    response = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout, follow_redirects=False)
    response.raise_for_status()
    try: data = response.json()
    except ValueError: return response.text
    if isinstance(data, dict) and "output" in data: return data
    if isinstance(data, str): return data
    raise ValueError("HTTP agent must return plain text or a JSON object containing 'output'")


def _local_endpoint(endpoint: str) -> tuple[str, str]:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Endpoint must be an HTTP(S) URL without embedded credentials")
    hostname = parsed.hostname.lower()
    try:
        loopback = ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        loopback = hostname == "localhost"
    if not loopback:
        raise ValueError("This local-first release only permits localhost/loopback endpoints. Remote endpoint support requires an explicit secure deployment configuration.")
    base = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    return base, parsed.path or "/agent"


def discover_http_agent(endpoint: str, timeout: float = 5) -> dict[str, Any]:
    """Probe conventional /health and /manifest routes without invoking the agent."""
    if not 0.1 <= float(timeout) <= 20:
        raise ValueError("Discovery timeout must be between 0.1 and 20 seconds")
    base, _ = _local_endpoint(endpoint)
    result: dict[str, Any] = {"endpoint": endpoint, "reachable": False, "manifest_found": False, "capabilities": [], "protocol_version": None, "checks": []}
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        for route, key in (("/health", "health"), ("/manifest", "manifest")):
            try:
                response = client.get(base + route)
                result["checks"].append({"route": route, "status_code": response.status_code})
                if key == "health" and response.is_success:
                    result["reachable"] = True
                    try: result["health"] = response.json()
                    except ValueError: result["health"] = response.text[:500]
                if key == "manifest" and response.is_success:
                    data = response.json()
                    if not isinstance(data, dict): raise ValueError("Manifest must be a JSON object")
                    caps = data.get("capabilities", [])
                    if not isinstance(caps, list) or not all(isinstance(x, str) for x in caps):
                        raise ValueError("Manifest capabilities must be a list of strings")
                    result.update({"manifest_found": True, "capabilities": sorted(set(caps)), "protocol_version": data.get("protocol_version", "1.0"), "manifest": data})
                    result["reachable"] = True
            except (httpx.HTTPError, ValueError) as exc:
                result["checks"].append({"route": route, "error": f"{type(exc).__name__}: {exc}"})
    if not result["reachable"]:
        raise ValueError("Could not verify the agent. Implement GET /health, or provide a compatible local HTTP endpoint. Details: " + str(result["checks"]))
    return result


def test_http_agent(endpoint: str, timeout: float = 5) -> dict[str, Any]:
    """Connection test uses discovery routes only; it never runs a paid task."""
    return discover_http_agent(endpoint, timeout)


def describe_protocol() -> dict[str, Any]:
    return {
        "protocol_version": "1.0",
        "required_request_fields": ["input"],
        "optional_request_fields": ["task_id", "context", "resources", "metadata"],
        "response": {"output": "string", "tool_calls": "array (optional)", "usage": "object (optional)", "metadata": "object (optional)"},
        "capabilities": ["text_input", "document_input", "tools", "stateful", "streaming", "usage_reporting"],
    }
