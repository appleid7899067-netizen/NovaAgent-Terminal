# ADR 0001: Multi-Agent Routing via Channel Instances

**Date:** 2026-10-31
**Status:** Accepted
**Author:** Sally (Astra Mode)

---

## Context

NovaAgent operates as a **modular monolith** with multiple agents registered in an `AgentRegistry`. Agents need to:

1. **Discover** each other at runtime
2. **Delegate** tasks to specialized agents
3. **Communicate** across agent boundaries
4. **Maintain** conversation context across delegations

The original design used a single global channel for all agent communication. As the system grew, this created:

- **Tight coupling** — all agents shared one message bus
- **No isolation** — team conversations leaked into each other
- **Routing ambiguity** — unclear which agent should handle which message
- **Testing difficulty** — hard to isolate agent interactions in tests

---

## Decision

We adopt **Channel Instances** as the primary routing primitive for multi-agent communication.

### Core Concepts

| Concept | Responsibility |
|---------|----------------|
| `ChannelInstance` | Isolated message bus with explicit membership (binding, members, peers) |
| `AgentRegistry` | Source of truth for agent profiles and capabilities |
| `AgentRouter` | Maps incoming messages → target channel instance → target agent |
| `Team` / `Roster` | Declarative grouping of agents for a purpose |

### Routing Flow

```
Incoming Request
       │
       ▼
AgentRouter.resolve(request)
       │
       ├──▶ Explicit channel_id? ──▶ ChannelInstance.get(channel_id)
       │
       └──▶ Team/roster specified? ──▶ ChannelInstance.get_or_create(team)
                    │
                    ▼
         ChannelInstance.route_to_agent(message)
                    │
                    ▼
            Target Agent.handle(message)
```

### Channel Instance Types

| Type | Creation | Use Case |
|------|----------|----------|
| **Legacy Global** | Auto-created at startup | Backward compat; single-agent deployments |
| **Team Channel** | `get_or_create(team_id)` | Multi-agent teams with shared context |
| **Ad-hoc Channel** | `create(peers=[...])` | One-off delegations, peer-to-peer |
| **Direct Channel** | `create(binding=agent_id)` | 1:1 agent communication |

---

## Consequences

### Positive

- **Isolation** — Team conversations don't leak
- **Explicit routing** — Clear ownership of message handling
- **Testability** — Can inject mock channel instances per test
- **Scalability** — Channels can be distributed later without API change
- **Observability** — Per-channel metrics, logs, tracing

### Negative

- **More objects** — ChannelInstance lifecycle management added
- **Migration cost** — Legacy code using global channel needs update
- **Complexity** — Router logic must handle multiple channel types

---

## Implementation Notes

### Key Files

| File | Role |
|------|------|
| `agent/routing/router.py` | `AgentRouter` — core routing logic |
| `agent/team/team.py` | `Team`, `Roster` — declarative team definitions |
| `channel/channel_instances.py` | `ChannelInstance`, `ChannelRegistry` |
| `agent/registry/registry.py` | `AgentRegistry` — agent discovery |

### Migration Path

1. **Phase 1** (current): ChannelInstance exists alongside global channel; new code uses explicit channels
2. **Phase 2**: Deprecate global channel accessor; warn on use
3. **Phase 3**: Remove global channel; all routing via ChannelInstance

---

## Related

- **GLOSSARY.md** entries: `ChannelInstance`, `AgentRouter`, `Team`, `Roster`, `AgentRegistry`
- **Future ADR**: Channel Instance distribution (cross-process, cross-host)
- **Future ADR**: Agent delegation protocol (request/response, streaming, cancellation)

---

## Checklist

- [x] ChannelInstance class implemented
- [x] ChannelRegistry manages lifecycle
- [x] AgentRouter routes to ChannelInstance
- [x] Team/Roster declarative API
- [ ] Global channel deprecation warning
- [ ] Integration tests for multi-team isolation
- [ ] Observability hooks (metrics per channel)

---

*This ADR records the architectural decision. Implementation details live in code; this document captures the **why**.*