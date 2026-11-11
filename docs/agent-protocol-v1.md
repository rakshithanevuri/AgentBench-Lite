# AgentBench Lite Agent Protocol v1.0

AgentBench Lite evaluates agents through adapters. An agent can be built with any framework; it does not need to install AgentBench Lite. The HTTP adapter sends one JSON request to the configured local endpoint.

## Request

```json
{
  "protocol_version": "1.0",
  "task_id": "question-01",
  "input": "What does the document say about retention?",
  "context": {"suite_name": "policy-qa", "suite_version": "1.0", "task_metadata": {}},
  "resources": [
    {"id": "policy", "name": "policy.txt", "mime_type": "text/plain", "content": "Retention is seven years."}
  ],
  "metadata": {"tags": ["document-qa"]}
}
```

`input` is the only required field. `task_id`, `context`, `resources` and `metadata` are optional. Resource content may be supplied as `content` for text or `content_base64` for binary content. Keep each resource below 5 MB. Resource IDs referenced by a task are the only resources sent to that task; when no IDs are specified, all suite resources are sent.

## Response

```json
{
  "output": "The retention period is seven years.",
  "tool_calls": [{"name": "document_search", "arguments": {"query": "retention"}}],
  "usage": {"input_tokens": 120, "output_tokens": 18, "total_tokens": 138},
  "metadata": {"sources": ["policy.txt"], "source_count": 1}
}
```

Only `output` is required. Usage and tool calls are agent-reported telemetry, not independently verified facts. Do not claim correctness based on telemetry alone.

## Capabilities

Agent registrations may declare `text_input`, `document_input`, `tools`, `stateful`, `streaming`, and `usage_reporting`. A suite can declare `required_capabilities`. ABL rejects an incompatible run before execution. `text_input` is treated as the baseline capability for every registered agent. Only declare capabilities the agent genuinely supports.

## Security and scope

This release's HTTP adapter intentionally permits only localhost/loopback endpoints. Remote endpoints, authentication, streaming and stateful session orchestration are not enabled yet. Never expose the local API to an untrusted network. Only load trusted local Python adapter code.


## Optional capability manifest (0.3)

An agent may expose `GET /manifest` on the same origin as its task endpoint. AgentBench uses it during onboarding; it does not call the model. Example:

```json
{
  "protocol_version": "1.0",
  "name": "My document agent",
  "capabilities": ["text_input", "document_input", "usage_reporting"],
  "input": {"modalities": ["text"], "resources": ["text/plain"]},
  "response": {"required": ["output"], "optional": ["tool_calls", "usage", "metadata"]}
}
```

`GET /health` should return a successful status when the agent is ready. `/manifest` is optional: agents without it can be configured manually. Capability declarations are developer-provided claims, not proof; benchmark execution validates the integration and evaluator checks assess behaviour.

AgentBench's **Discover capabilities** and **Test connection** actions call only `/health` and `/manifest`. They do not send a task to `/agent`, so they do not trigger a model response or consume LLM tokens.
