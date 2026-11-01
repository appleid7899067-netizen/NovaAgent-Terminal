# NovaAgent-Clean — Glossary (Ubiquitous Language)

> **Purpose**: คำศัพท์มาตรฐานที่ทีมพัฒนาและ AI ใช้ร่วมกันในโค้ด ตั้งใจให้ **คำหนึ่ง = ความหมายหนึ่ง** ไม่มีคำสองความหมาย ความหมายสองคำ
>
> **Maintenance**: อัปเดตเมื่อมีคำใหม่ เข้ามา หรือขอบเขตเปลี่ยน — อ้างอิงจากโค้ดจริง (`agent/`, `bridge/`, `channel/`, `config/`) ไม่ใช่ความคิดในหัว
>
> **Cross-references**: `[Term](#term)` ลิงก์ภายในไฟล์นี้ | `[Term](../path/file.py)` ลิงก์ไปโค้ดต้นทาง

---

## 🏗️ Core Domain — Agent Runtime

### Agent
**Definition**: หน่วยทำงานอิสระที่มี **workspace แยกต่างหาก** `AgentProfile` (id, name, workspace, model, skills, knowledge) — จัดการโดย `AgentRegistry`
- **Identity**: `id` = string 1-64 chars `[A-Za-z0-9_-]` (stable, ไม่เปลี่ยน)
- **Workspace**: ไดเรกทอรีที่ agent เก็บ memory, knowledge, config ของตัวเอง — default agent ใช้ instance root (`~/cow`), agent อื่นอยู่ที่ `agents/<id>/`
- **Lifecycle**: `enabled` (bool) — disabled agent ไม่ตอบคำขอ; `default_agent_id` = agent ที่รับ request ที่ไม่ได้ระบุเป้าหมาย
- **Code**: `agent/registry.py:30-74` (`AgentProfile`), `agent/registry.py:168-348` (`AgentRegistry`)

### AgentRegistry
**Definition**: Thread-safe registry ของ agent profiles ทั้งหมดใน instance — โหลดจาก `config.json` + `agents/team.json` (roster file)
- **Responsibilities**: CRUD profiles, validate uniqueness (id, workspace), resolve default, pin/unpin for tests
- **Singleton pattern**: `get_agent_registry()` คืน instance เดียวต่อ process, rebuild เมื่อ config signature เปลี่ยน
- **Code**: `agent/registry.py:168-426`

### DEFAULT_AGENT_ALIAS
**Value**: `"default"` — reserved alias ที่ `AgentRegistry.get_addressed()` แปลเป็น default agent จริง (ไม่ว่าจะมี id อะไร)
- **Use case**: Remote callers เรียก default agent โดยไม่ต้องรู้ id จริง
- **Code**: `agent/registry.py:23`

### Team / Roster
**Definition**: ชุด agent profiles + `default_agent_id` + `channel_instances` ที่เก็บใน `agents/team.json` (แยกจาก `config.json` เพื่อกัน race condition)
- **Keys**: `TEAM_KEYS = ("agents", "default_agent_id", "channel_instances")`
- **Migration**: `team.migrate()` ย้ายจาก `config.json` ครั้งเดียวตอน startup; `team.write()` เขียน atomic + bootstrap legacy channels
- **Code**: `agent/team.py:1-242`

---

## 🌉 Bridge Layer

### Bridge
**Definition**: Facade เดิมของ COW — จัดการ bot providers (chat, voice, translate) แบบ singleton; ต่อยอดด้วย `AgentBridge` สำหรับ agent-based conversations
- **Key fields**: `btype` (map typename → provider const), `bots` (cached instances), `_agent_bridge` (lazy init)
- **Code**: `bridge/bridge.py:12-197`

### AgentBridge
**Definition**: Adapter ระหว่าง Bridge เดิมกับ Agent system — สร้าง/จัดการ `Agent` instances ต่อ session, routing, delegation, scheduler, evolution trigger
- **Core maps**: `_agent_instances: Dict[Tuple[agent_id, session_id], Agent]`, `_default_agents`, `agents` (backward-compat view)
- **Key methods**:
  - `route_context(context)` → resolve agent_id จาก channel instance binding
  - `create_agent()` → build `Agent` พร้อม tools, memory, skills
  - `agent_reply()` → orchestrate agent run (steer, cancel, delegation, team speaker resolution)
  - `_seed_team_members()` → reconcile channel instance roster onto session prefs
- **Code**: `bridge/agent_bridge.py:620-1100+`

### AgentLLMModel
**Definition**: LLMModel adapter ที่ใช้ COW bot infrastructure — รองรับ **model routing hierarchy** (session override > agent default > global config > fallback chain)
- **Routing precedence**:
  1. `_fallback_model` (engaged fallback outranks everything)
  2. `_session_model` / `_session_provider` (per-conversation pin)
  3. `_agent_model` / `_agent_provider` (per-agent pin)
  4. `use_linkai` + `linkai_api_key`
  5. configured `bot_type`
  6. model-name inference (`_primary_bot_type`)
- **Fallback chain**: `chat_fallback.chain[]` — walk ลิงก์ต่อลิงก์ (wrap-around, 2 passes max)
- **Tool routing**: opt-in cheap/free route สำหรับ tool calls (`agent_tool_routing_enabled`)
- **Code**: `bridge/agent_bridge.py:74-617`

---

## 🚦 Routing & Channels

### AgentRouter
**Definition**: Resolves inbound request → agent_id โดยอิง **channel instance binding** (`bound_agent_id` ใน context) ไม่มี binding table แยก
- **Resolution order**:
  1. Explicit `agent_id` ใน context (console request) — ต้อง enabled
  2. `bound_agent_id` จาก channel instance — ต้อง enabled
  3. Default agent
- **Error policy**: Route ที่ชี้ agent missing/disabled = `AgentUnavailableError` (hard fail, ไม่ fallback เงียบ ๆ)
- **Code**: `agent/routing.py:25-78`
- **ADR**: [ADR-001](../docs/adr/ADR-001-multi-agent-routing-via-channel-instances.md) — routing flow decision

### ChannelInstance
**Definition**: หนึ่ง channel ที่รันจริง — มี `instance_id`, `channel_type`, `agent_id` (owner), `credentials` (per-instance override), `members` (teammates), `peers` (cross-process teammates)
- **Legacy vs Explicit**:
  - Legacy: synthesized จาก `channel_type` list + flat credentials ใน `config.json` (single-agent mode)
  - Explicit: `channel_instances` array ใน `team.json` (multi-agent mode)
- **Multi-instance ready**: `MULTI_INSTANCE_READY` = {FEISHU, DINGTALK, QQ, TELEGRAM, SLACK, DISCORD, WEIXIN, WECOM_BOT}
- **Code**: `channel/channel_instances.py:146-173` (`ChannelInstance`), `resolve_channel_instances()` line 272
- **ADR**: [ADR-001](../docs/adr/ADR-001-multi-agent-routing-via-channel-instances.md) — routing primitive decision

### ChannelInstance Binding
**Definition**: `agent_id` ใน `ChannelInstance` = owner agent ที่รับทุก inbound message บน channel นั้น — routing ใช้ค่านี้ผ่าน `context["bound_agent_id"]`
- **Members**: teammates ที่ owner อาจ delegate ให้ (via `@mention` หรือ `agent_delegate` tool) — ไม่รวม owner เอง
- **Peers**: teammates ที่รันใน process อื่น — transport จะ resolve ด้วย id นี้
- **Code**: `channel/channel_instances.py:152-169`

---

## 🧠 Memory System

### MemoryManager
**Definition**: High-level interface สำหรับ memory operations — hybrid search (vector + keyword), sync จากไฟล์, flush conversation summary
- **Scopes**: `shared` (MEMORY.md, knowledge/), `user` (per-user daily), `session` (ephemeral)
- **Storage**: `MemoryStorage` (SQLite + FTS5 + vector via sqlite-vec)
- **Chunker**: `TextChunker` — markdown-aware (`chunk_markdown`) + plain text fallback
- **Embedding**: `EmbeddingProvider` (optional — ไม่มี = keyword-only)
- **Reranker**: `Reranker` (optional — reorder candidates)
- **Temporal decay**: daily files (`memory/YYYY-MM-DD.md`) decay exponentially (half-life 30 days); MEMORY.md, knowledge = evergreen
- **Hit boost**: opt-in popularity/recency nudge (log2(hits) + recency decay 7 days, capped)
- **Code**: `agent/memory/manager.py:63-918`

### MemoryConfig
**Definition**: Configuration สำหรับ memory — paths, chunk sizes, weights, embedding provider/model
- **Key params**: `chunk_max_tokens`, `chunk_overlap_tokens`, `vector_weight`, `keyword_weight`, `max_results`, `min_score`, `sync_on_search`
- **Code**: `agent/memory/config.py`

### MemoryChunk / SearchResult
**Definition**: หน่วยข้อมูลใน index — `MemoryChunk` = stored unit (id, path, lines, text, embedding, hash, metadata); `SearchResult` = ranked hit (path, lines, score, snippet, source, user_id)
- **Code**: `agent/memory/storage.py` (not read but referenced)

### ConversationStore
**Definition**: Per-agent session store (transcripts) — จัดการโดย `get_conversation_store(workspace)` คืน store ผูกกับ agent workspace
- **Code**: `bridge/agent_bridge.py:751-755`

---

## 📚 Knowledge System

### KnowledgeService
**Definition**: Filesystem-backed knowledge base service — CRUD documents/categories, rebuild `index.md`, graph extraction, reindex queue
- **Layout**: `knowledge/index.md`, `knowledge/log.md`, `knowledge/<category>/<slug>.md`
- **Protected**: `index.md`, `log.md` (ไม่ให้ edit/delete ผ่าน API)
- **Index rebuild**: `rebuild_index_md()` สแกน tree → generate links + preserve hand-written summaries (— summary suffix)
- **Reindex**: background worker queue (`_reindex_queues`) — coalesce bursts, `wait_for_reindex()` สำหรับ tests
- **Graph**: `build_graph()` parse `[[link](path.md)]` cross-refs → nodes + links for visualization
- **Code**: `agent/knowledge/service.py:28-855`

---

## 🌐 Web Console (Channel Web)

### WebChannel
**Definition**: Web server (web.py) ที่ serve single-page console + REST API — routes defined in `web_channel.URLS`
- **Key routes**:
  - `/` `/chat` → `ChatHandler` (SPA shell)
  - `/api/*` → various handlers (agents, channels, chat, config, files, knowledge, memory, models, scheduler, sessions, skills, update, workspace)
  - `/v1/chat/completions` `/v1/models` → OpenAI-compatible endpoints
  - `/stream` `/poll` `/cancel` → streaming chat
- **Auth boundary**: `/config` real route (not `/api/config`); protected endpoints on 127.0.0.1:17009
- **Code**: `channel/web/web_channel.py:1-210`

### WebMessage / SSEStreamState
**Definition**: Core types สำหรับ web channel messaging และ SSE streaming state
- **Code**: `channel/web/core/_common.py`

---

## ⚙️ Config & Security

### Config (conf())
**Definition**: Global configuration singleton — reads `config.json` + env overrides; คีย์สำคัญ:
- `agent_workspace` (instance root)
- `bot_type`, `model` (global LLM routing)
- `use_linkai`, `linkai_api_key`
- `channel_type` (legacy), `channel_instances` (in team.json)
- `knowledge` (bool), `enable_thinking`, `reasoning_effort`
- **Code**: `config.py`, `config.json`

### AuthBoundary
**Definition**: ขอบเขตการ authenticate — แยกเป็น:
1. **Bridge/Channel level**: channel credentials (per-instance in `channel_instances`)
2. **Web API level**: `/auth/*` handlers, protected endpoints on localhost only
3. **Agent Runtime level**: `AgentRegistry` + `AgentRouter` enforce agent enabled/disabled
- **Principle**: ไม่มี single auth god module — แต่ละ layer จัดการของตัวเอง

### Secrets
**Definition**: Sensitive values (API keys, tokens) — เก็บใน `config.json` (central) + per-instance credentials; **ห้าม** log, commit, หรือส่งผ่าน API
- **App Passwords**: Gmail App Password เคยหลุดใน chat → ต้อง revoke + reissue, ไม่เก็บค่าจริงใน memory/log

---

## 🛠️ Skills & Tools

### Skill
**Definition**: Packaged capability (code + metadata) ที่ agent โหลดได้ — จัดการโดย `SkillManager`, `SkillRegistry`
- **Registry**: `agent/skills/` + `skills/` (workspace-level)
- **Lock file**: `skills-lock.json` (pinned versions)
- **Installation**: `channel/web/api/skills.py` handlers (`_install_skill_for_agent`)
- **Code**: `agent/skills/`, `channel/web/api/skills.py`

### Tool
**Definition**: Callable function ที่ agent ใช้ผ่าน tool-calling — จัดการโดย `ToolManager`, `ToolsHandler`
- **Categories**: filesystem, web, scheduler, memory, knowledge, skills, subagent, etc.
- **Code**: `agent/tools/`, `channel/web/api/skills.py` (`ToolsHandler`)

### MCP (Model Context Protocol)
**Definition**: External tool/server integration — `McpServersHandler`, `McpServerTestHandler`; config ใน `mcp.json` + `mcp-config.json`
- **Code**: `channel/web/api/skills.py` (MCP handlers), `mcp-installs/`

---

## 🤝 Multi-Agent & Delegation

### Delegation
**Definition**: Owner agent ส่งงานให้ teammate (ใน team หรือ cross-process peer) — ผ่าน `agent_delegate` tool หรือ `@mention`
- **Session scoping**: delegated turn runs in private session, carries `delegation_members` (seed-once, never overwrite)
- **Peer transport**: `agent.multiagent.transport` — register peers, invoke remote
- **Code**: `bridge/agent_bridge.py:951-1000+` (`_speak_on_peer`, `_peer_speaker`)
- **ADR**: [ADR-001](../docs/adr/ADR-001-multi-agent-routing-via-channel-instances.md) — delegation protocol follow-up (ADR-002 planned)

### Team Conversation
**Definition**: Channel instance ที่มี `members` > 0 — ทุก inbound message ถูก route ให้ owner, owner อาจ delegate ให้ teammates
- **Roster sync**: `_seed_team_members()` authoritative reconcile (channel instance wins) vs delegation seed-once
- **Runtime retirement**: roster เปลี่ยน → `_retire_session_runtimes()` drop cached agent instances เพื่อ rebuild tool list
- **Code**: `bridge/agent_bridge.py:757-870`

---

## 🔄 Evolution & Scheduler

### Evolution Trigger
**Definition**: Idle-time self-evolution background thread — `start_evolution_trigger(AgentBridge)` daemon thread
- **Code**: `bridge/agent_bridge.py:661-665`, `agent/evolution/trigger.py`

### Scheduler
**Definition**: Per-agent cron/interval/once tasks — `init_scheduler(bridge, workspace, agent_id)` eager-start at bridge init
- **Persistence**: per-agent workspace; runs ถูก bind กับ agent_id
- **Code**: `agent/tools/scheduler/integration.py`, `channel/web/api/scheduler.py`

---

## 📦 Platform Contract (v1)

### Resource Model
**Definition**: Canonical resources สำหรับ platform API — agents, sessions, messages, artifacts, skills, knowledge, channels, scheduler, memory
- **Versioning**: `/api/v1/` prefix, OpenAPI spec, request IDs, pagination, error contract
- **Auth scopes**: Agent Runtime, Memory/Knowledge, Control Plane (separate, no god module)
- **Health/Readiness**: `/api/health`, `/api/readiness`
- **SSE envelope**: structured events for streaming
- **Code**: `platform_contract/`, `platform_contract_tests/`

---

## 📐 Architectural Patterns (Cross-cutting)

### Singleton (process-wide)
- `Bridge` (`@singleton` decorator)
- `AgentRegistry` (`get_agent_registry()`)
- `AgentRouter` (`get_agent_router()`)
- `KnowledgeService._reindex_queues` (class-level)

### Lazy Initialization
- `AgentLLMModel.bot` (rebuild เมื่อ model/bot_type เปลี่ยน)
- `AgentBridge._agent_bridge` (first call to `get_agent_bridge()`)
- `KnowledgeService._memory_manager` (first write/read)

### Atomic Write + Reconcile
- `common.atomic_write.write_text_atomic()` — all file writes
- `team.write()` → roster file atomic + bootstrap legacy
- `KnowledgeService` rebuild index.md before reindex

### Graceful Degradation
- Vector search fails → keyword-only (MemoryManager)
- Rerank fails → keep fused order (MemoryManager)
- Embedding batch fails → leave index untouched, retry next sync (MemoryManager.sync)
- Channel not multi-instance-ready → log + run as single (ChannelInstances)

---

## 🔗 Cross-Reference Index

| Term | Primary Definition | Code Reference | ADR |
|------|-------------------|----------------|-----|
| Agent | [Core Domain](#agent) | `agent/registry.py:30` | — |
| AgentProfile | [Core Domain](#agent) | `agent/registry.py:30-74` | — |
| AgentRegistry | [Core Domain](#agentregistry) | `agent/registry.py:168` | — |
| AgentRouter | [Routing](#agentrouter) | `agent/routing.py:25` | [ADR-0001](../docs/adr/0001-multi-agent-routing-via-channel-instances.md) |
| AgentBridge | [Bridge](#agentbridge) | `bridge/agent_bridge.py:620` | — |
| AgentLLMModel | [Bridge](#agentllmmodel) | `bridge/agent_bridge.py:74` | — |
| Bridge | [Bridge](#bridge) | `bridge/bridge.py:12` | — |
| ChannelInstance | [Channels](#channelinstance) | `channel/channel_instances.py:146` | [ADR-0001](../docs/adr/0001-multi-agent-routing-via-channel-instances.md) |
| ConversationStore | [Memory](#conversationstore) | `bridge/agent_bridge.py:751` | — |
| KnowledgeService | [Knowledge](#knowledgeservice) | `agent/knowledge/service.py:28` | — |
| MemoryManager | [Memory](#memorymanager) | `agent/memory/manager.py:63` | — |
| Team / Roster | [Core Domain](#team--roster) | `agent/team.py:1` | — |
| WebChannel | [Web Console](#webchannel) | `channel/web/web_channel.py:87` | — |
| Delegation | [Multi-Agent](#delegation) | `bridge/agent_bridge.py:951` | — |
| Evolution Trigger | [Evolution](#evolution-trigger) | `agent/evolution/trigger.py` | — |
| Scheduler | [Scheduler](#scheduler) | `agent/tools/scheduler/integration.py` | — |

---

## 📝 Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-10-31 | Initial glossary extracted from codebase | Sally (Domain Modeling) |

---

> **Next steps**: เมื่อมีคำใหม่ หรือขอบเขตเปลี่ยน (เช่น platform contract v2, marketplace) → อัปเดตไฟล์นี้ทันที พร้อม commit message อธิบาย *why* เปลี่ยน