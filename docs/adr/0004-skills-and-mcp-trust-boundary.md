# ADR 0004: Skills and MCP Trust Boundary

**Date:** 2026-10-31
**Status:** Proposed
**Author:** Sally (Astra Mode)

---

## Context

NovaAgent has two related but distinct extension mechanisms:

- **Skills** are Markdown guidance loaded into the model's prompt by the skill loader/manager. They can describe workflows, but are not themselves callable tools and do not create operating-system isolation.
- **Tools** are callable functions registered with the agent runtime. MCP client integrations connect to configured external servers and expose their tools through the local tool interface.

Conflating these mechanisms creates a dangerous permission assumption: prose in a skill, a tool description, or a remote server response must not be treated as proof that an operation is authorized or sandboxed. MCP servers can perform side effects in their own environment, and tool-name heuristics are not a security boundary.

The architecture must preserve agent/workspace isolation, keep credentials out of prompts and logs, and avoid granting a remote integration broader access than its configured purpose.

## Decision

**Proposed:** Keep a hard conceptual boundary between guidance and executable capability:

1. A Skill is untrusted instructional content. Loading or selecting a skill does not grant additional tools, permissions, or access by itself.
2. A Tool is an executable capability. Its registration and execution must remain subject to the runtime's permission checks and the relevant agent/workspace boundary.
3. An MCP server is an external tool provider, not a trusted authority. Its tool names, descriptions, results, and embedded instructions are data; they cannot override NovaAgent policy or user authorization.
4. MCP configuration is scoped to the owning agent/workspace where supported. Credentials are supplied only to the intended server and must not be logged or exposed to model-visible output.
5. Remote MCP connections and local `stdio` servers require explicit configuration. Deployments should restrict endpoints, commands, environment variables, and exposed tools to the minimum necessary. A permission-mode heuristic is defense in depth, not a sandbox.
6. Any future skill or MCP management API must validate inputs, preserve workspace ownership, and use the same authorization boundary as other control-plane mutations; text instructions must never bypass that boundary.

This ADR records a proposed boundary and reviewable principles. It does not claim that all safeguards above are already enforced by the current implementation.

## Consequences

### Positive
- Clear separation between prompt guidance and executable capability.
- Reduces prompt-injection and confused-deputy risks from skill files and remote MCP output.
- Makes workspace isolation and authorization explicit review requirements for future integrations.

### Negative
- Security depends on the actual tool permission and configuration paths; documentation alone does not enforce the boundary.
- Existing permissive defaults or incomplete authorization may require separate implementation work and migration decisions.
- Additional validation and auditing may add configuration and operational friction.

### Risks / Mitigations
- **Risk:** A deployment mistakes tool-name heuristics for a sandbox. **Mitigation:** Document the limit and test authorization at the actual execution boundary.
- **Risk:** A skill or MCP result contains hostile instructions. **Mitigation:** Treat external content as untrusted data; keep policy and permissions outside model-authored content.
- **Risk:** A configured server receives excessive credentials or capabilities. **Mitigation:** Scope credentials and exposed tools per workspace and use explicit allowlists where available.
- **Risk:** Proposed rules are mistaken for implemented controls. **Mitigation:** Keep status Proposed until reviewed and track enforcement separately with tests.

## Implementation Notes

Verified current behavior includes prompt-based loading of skill Markdown, workspace-aware MCP configuration lookup, MCP server startup and tool wrapping, and parameter-level permission checks. Some defaults are permissive; this ADR does not certify them as secure. Before changing defaults, inspect existing deployments and add compatibility tests.

Relevant code includes:

- `agent/skills/loader.py`, `agent/skills/manager.py`, `agent/prompt/builder.py`
- `agent/tools/tool_manager.py`
- `agent/tools/mcp/service.py`, `agent/tools/mcp/mcp_client.py`, `agent/tools/mcp/mcp_tool.py`
- `agent/permission/policy.py`

Follow-up work, if this proposal is accepted:

- Add tests proving skills cannot register or invoke tools merely through Markdown content.
- Add contract tests for per-workspace MCP configuration and credential isolation.
- Review safe defaults for `stdio` command allowlists and remote URL validation without silently breaking local/LAN use.
- Verify authorization for any MCP/skill management endpoint before enabling mutations.

## Related

- [GLOSSARY.md — Skills & Tools](../../GLOSSARY.md#-skills--tools)
- [ADR 0001 — Multi-Agent Routing](0001-multi-agent-routing-via-channel-instances.md)
- [ADR 0002 — Platform Contract v1](0002-platform-contract-v1-execution-vocabulary-run-lifecycle.md)
- [ADR 0003 — Memory Architecture](0003-memory-architecture-conversation-store-vector-backend-summarization.md)

---

*This ADR separates verified current behavior from proposed policy; acceptance requires review of the trade-offs and enforcement plan.*
