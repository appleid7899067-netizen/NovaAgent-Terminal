# MCP Orchestrator

A knowledge page describing the MCP orchestrator skill design and integration points. This skill acts as a central router for external service calls, enabling parallel requests, caching, retry policies and adding observability (logging/metrics) for reliability. It is intended to work with MCP-enabled agents and external APIs.

- Keywords: MCP, orchestration, parallel calls, caching, retries, circuit breaker, observability
- Related concepts: MCP SDK, model context protocol, tooling for external services
