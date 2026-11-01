# ADR 0002: Platform Contract v1 — Execution Vocabulary & Run Lifecycle

**Date:** 2026-10-31
**Status:** Accepted
**Author:** Sally (Astra Mode)

---

## Context

NovaAgent needs a **transport-neutral contract** that describes *what a unit of agent work is* — independent of HTTP, WebSocket, CLI, or any specific channel. Previously:

- Work was implicitly tied to the HTTP request/response cycle in `bridge/bridge.py`
- No first-class representation of "a run" existed — only messages and sessions
- Idempotency, cancellation, and streaming were handled ad-hoc per transport
- Adding a new transport (e.g. MCP, scheduler, subagent) required duplicating logic

**Forces at play:**
- Multiple entry points: web UI, CLI, scheduler, MCP servers, subagent delegation
- Need for **idempotent retries** (network flakiness, user double-click)
- Need for **cancellation** (user stops generation, timeout, parent run cancelled)
- Need for **audit trail** (what ran, when, input/output, errors)
- Must not pretend in-memory storage is durable — explicit `InMemoryRunStore` is a v1 proof-of-concept only

---

## Decision

We introduce **Platform Contract v1** — a minimal, versioned vocabulary for *runs* as the atomic unit of execution.

### Core Entities

| Entity | Purpose |
|--------|---------|
| `Run` | One addressable, persisted unit of agent work (delegated task, subagent spawn, scheduled job) |
| `RunState` | Explicit lifecycle: `queued → running → succeeded | failed | cancel_requested → cancelled` |
| `RunEvent` | Immutable append-only event log per run (created, state transitions, tool calls) |
| `AgentRef` / `SessionRef` | Opaque identifiers — contract does not dictate their format |
| `IdempotencyKey` | Client-provided key scoped to `(agent_id, key)` for safe retries |

### Run State Machine

```
QUEUED
  ├─▶ RUNNING
  │       ├─▶ SUCCEEDED (requires output)
  │       ├─▶ FAILED (requires error)
  │       └─▶ CANCEL_REQUESTED ──▶ CANCELLED
  ├─▶ CANCEL_REQUESTED ──▶ CANCELLED
  └─▶ CANCELLED
```

**Terminal states:** `SUCCEEDED`, `FAILED`, `CANCELLED` — no further transitions allowed.

### RunService API (Application Service)

```python
class RunService:
    def create_run(agent_id, session_id, input_text, *, idempotency_key=None) -> Run
    def transition(run_id, target_state, *, output=None, error=None) -> Run
    def cancel(run_id) -> Run  # queued→cancelled, running→cancel_requested
```

- **Idempotency:** `create_run` with same `(agent_id, idempotency_key)` returns existing run
- **Validation:** Empty input rejected; `SUCCEEDED` requires `output`; `FAILED` requires `error`
- **Events:** Every state change emits a `RunEvent` (sequence-numbered, ordered)
- **Store boundary:** `InMemoryRunStore` implements the repository interface; SQLite/queue backend swappable later

### Versioning

- `CONTRACT_VERSION = "1.0"` embedded in every serialized `Run.to_dict()` and `RunEvent.to_dict()`
- Breaking changes → `2.0` with new ADR; non-breaking additions stay in `1.x`

---

## Consequences

### Positive
- **Transport agnostic** — HTTP, WebSocket, MCP, scheduler, CLI all speak the same `Run` language
- **Explicit lifecycle** — no more "is it done?" ambiguity; state machine is the source of truth
- **Idempotency built-in** — safe retries without duplicate work
- **Cancellation as first-class** — not an afterthought; propagates via `CANCEL_REQUESTED`
- **Audit trail** — `RunEvent` log enables debugging, replay, observability
- **Testable** — `RunService` takes a `store` dependency; swap `InMemoryRunStore` for fakes in tests

### Negative
- **More types** — `Run`, `RunState`, `RunEvent`, `AgentRef`, `SessionRef`, exceptions
- **In-memory only for v1** — not durable; a process restart loses all runs (by design, documented)
- **No streaming yet** — `RunEvent` is append-only log; streaming tokens requires separate channel (future ADR)

### Risks / Mitigations
| Risk | Mitigation |
|------|------------|
| In-memory store mistaken for production | Docstring + ADR explicitly: "proves semantics without pretending process memory is durable" |
| State machine too rigid | Transitions are explicit in code (`_ALLOWED_TRANSITIONS`); new states = new ADR |
| Idempotency key collisions | Scoped to `(agent_id, key)`; caller chooses key (e.g. request ID, hash of input) |
| Event log grows unbounded | v1 keeps in memory; persistent backend will add TTL / archival policy |

---

## Implementation Notes

### Key Files

| File | Role |
|------|------|
| `platform_contract/models.py` | `Run`, `RunState`, `RunEvent`, `AgentRef`, `SessionRef`, `CONTRACT_VERSION`, state machine |
| `platform_contract/run_service.py` | `RunService`, `InMemoryRunStore`, exceptions (`RunNotFound`, `IdempotencyConflict`, `InvalidRunTransition`) |
| `platform_contract/__init__.py` | Public exports |

### Migration Path
1. **Phase 1 (current):** `RunService` used by `bridge/agent_bridge.py` for HTTP runs; scheduler uses it for scheduled jobs
2. **Phase 2:** Subagent delegation creates child runs (`parent_run_id` in `conversation_store.py` runs table)
3. **Phase 3:** Persistent store (SQLite + WAL) implements same repository interface; `InMemoryRunStore` → test-only

### Checklist
- [x] `Run` entity with state machine
- [x] `RunService` with idempotent create, validated transitions, cancel
- [x] `InMemoryRunStore` with event log
- [x] `CONTRACT_VERSION` in all serialized output
- [ ] Persistent store implementation (separate ADR)
- [ ] Streaming token events (separate ADR)
- [ ] Integration tests: idempotency, cancellation, concurrent transitions

---

## Related

- **GLOSSARY.md** entries: `Run`, `RunState`, `RunEvent`, `RunService`, `InMemoryRunStore`, `IdempotencyKey`, `Platform Contract v1`
- **ADR 0001:** Multi-Agent Routing via Channel Instances (runs live in channels)
- **ADR 0003:** Memory Architecture (conversation store shares DB with run metadata)
- **Future ADR:** Persistent Run Store (SQLite/queue backend)
- **Future ADR:** Streaming Protocol (token-by-token via RunEvent stream)
- **External:** OpenAPI spec for `/api/v1/runs` (Contract v1 → HTTP mapping)

---

*This ADR records the architectural decision. Implementation details live in code; this document captures the **why**.*