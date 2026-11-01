# Architecture Decision Records (ADR) Index

> **Purpose**: Record significant architectural decisions for NovaAgent.
> **Format**: Markdown, one file per decision, numbered sequentially.
> **Location**: `docs/adr/NNNN-short-title.md`
> **Statuses**: Proposed | Accepted | Superseded | Deprecated

---

## ADR List

| # | Title | Status | Date | Supersedes |
|---|-------|--------|------|------------|
| [0001](0001-multi-agent-routing-via-channel-instances.md) | Multi-Agent Routing via Channel Instances | Accepted | 2026-10-31 | — |
| [0002](0002-platform-contract-v1-execution-vocabulary-run-lifecycle.md) | Platform Contract v1 — Execution Vocabulary & Run Lifecycle | Accepted | 2026-10-31 | — |
| [0003](0003-memory-architecture-conversation-store-vector-backend-summarization.md) | Memory Architecture — Conversation Store, Vector Backend, Summarization Pipeline | Accepted | 2026-10-31 | — |
| [0004](0004-skills-and-mcp-trust-boundary.md) | Skills and MCP Trust Boundary | Proposed | 2026-10-31 | — |

---

## How to Add a New ADR

1. **Copy template** → `docs/adr/NNNN-new-decision.md`
2. **Fill in**: Context, Decision, Consequences, Implementation Notes
3. **Update this index** — add row to table above
4. **Link from GLOSSARY.md** — add cross-reference in relevant glossary entries
5. **Commit** with message: `docs(adr): NNNN — short title`

---

## When to Write an ADR

Write an ADR when the decision:

- 🏗️ **Affects system architecture** (modules, boundaries, data flow)
- 🔄 **Has long-term consequences** (hard to reverse later)
- 🤝 **Requires team alignment** (multiple people need to understand)
- 📝 **Is not obvious from code alone** (the "why" matters)

**Don't write ADRs for**: tactical fixes, obvious choices, implementation details that don't affect architecture.

---

## ADR Template

```markdown
# ADR NNNN: Short Descriptive Title

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded | Deprecated
**Author:** Name

---

## Context

What is the problem? What forces are at play? What constraints exist?

## Decision

What did we decide? Be specific. Include diagrams if helpful.

## Consequences

### Positive
- Benefit 1
- Benefit 2

### Negative
- Cost 1
- Cost 2

### Risks / Mitigations
- Risk → Mitigation

## Implementation Notes

Key files, migration path, checklist.

## Related

- GLOSSARY.md entries
- Other ADRs
- External references
```

---

## Cross-Reference Map

| Domain Area | Related ADRs |
|-------------|--------------|
| Agent Runtime | 0001 |
| Bridge / LLM Routing | — |
| Memory System | — |
| Knowledge System | — |
| Web Console / API | — |
| Config / Security | — |
| Skills / Tools / MCP | — |
| Multi-Agent / Delegation | 0001 |
| Evolution / Scheduler | — |
| Platform Contract v1 | — |

*Update this table when adding ADRs.*