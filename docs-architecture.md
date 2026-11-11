# AgentBench Lite architecture (0.2)

```text
Dashboard / CLI
      |
FastAPI control plane ---- Benchmark suites (YAML / JSON resources)
      |
Evaluation service
      |-- compatibility validation
      |-- runner / protocol adapter
      |-- evaluator registry
      |-- trace + result persistence
      |
External agents (local Python adapter or localhost HTTP endpoint)
```

## Boundaries

AgentBench owns benchmark definitions, task/resource dispatch, evaluator selection, scoring, result storage, diagnostics, traces and comparisons. The agent owns its model, framework, prompts, retrieval, tools, memory and domain logic. The integration boundary is a versioned request/response protocol. Framework-specific logic belongs in an agent-side adapter, never in the benchmark service.

## Execution model

A benchmark suite contains metadata, required capabilities, shared resources and task cases. Before a run, the service checks that each selected agent declares the required capabilities. For each task, only referenced resources are sent; if `resource_ids` is empty, all suite resources are sent. The runner normalizes string/dict/AgentOutput responses, evaluates them, and persists output, reported telemetry, metadata, evaluator diagnostics and trace events.

## Evaluation model

Built-in checks are deterministic and offline. Weighted scores are computed from `check_weights`; pass/fail remains strict (all configured checks must pass). Operational telemetry (latency, reported token usage, tool calls) is separate from correctness. Custom checks can be registered in Python. No LLM judge runs by default.

## Persistence

SQLite + SQLModel. Schema upgrades are additive and preserve existing rows. Evaluation is synchronous in this release. A job queue, multi-user access control and remote deployment are deliberately deferred.

## Security boundary

The HTTP adapter accepts only localhost/loopback endpoints. This avoids turning the local evaluation service into an unrestricted SSRF proxy. Remote agents require a separately designed allowlist, DNS/IP validation, authentication and deployment threat model before enabling them.
