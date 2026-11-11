# Changelog

## 0.2.0 — Universal Agent Evaluation Framework

- Added protocol v1.0 and protocol discovery endpoint.
- Added declared agent capabilities and benchmark compatibility checks.
- Added suite-managed resources and task-level resource selection.
- Added JSON benchmark import API and dashboard workflow.
- Added weighted evaluator scores and detailed check diagnostics.
- Added deterministic JSON, tool-call, source-metadata and usage checks.
- Persisted agent metadata and evaluator details.
- Added additive SQLite migration for existing 0.1 workspaces.
- Expanded tests, protocol docs and generic HTTP agent example.

## 0.1.0

- Initial local-first evaluation workbench.

## 0.3.0 — Universal Agent Onboarding

- Added optional `/manifest` capability discovery during agent onboarding.
- Added non-invoking connection checks using `/health` and `/manifest`.
- Added manual capability fallback for agents without a manifest.
- Added live benchmark compatibility preview before evaluation.
- Added `/api/agents/discover`, `/api/agents/test-connection`, and `/api/compatibility`.
- Updated the generic example agent and onboarding/protocol documentation.
- Preserved the 0.2 data model and existing benchmark/evaluation workflows.
