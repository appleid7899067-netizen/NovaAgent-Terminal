# ADR 0003: Memory Architecture — Conversation Store, Vector Backend, Summarization Pipeline

**Date:** 2026-10-31
**Status:** Accepted
**Author:** Sally (Astra Mode)

---

## Context

NovaAgent needs **long-term memory** that survives restarts, supports hybrid search (vector + keyword), and stays performant as the corpus grows. The existing design had several gaps:

- **Conversation history** and **semantic memory** shared one SQLite file but with no clear separation of concerns
- **Vector search** was tightly coupled to a specific embedding provider (no backend abstraction)
- **Summarization** (daily memory flush) lived in the same class as search, making it hard to test or replace
- **CJK/mixed-language search** was unreliable — unicode61 tokenizer breaks CJK; trigram tokenizer requires SQLite 3.34+
- **Index corruption** from crashes or version mismatches could silently kill search
- **No reconciliation** — deleted files stayed in the index forever

**Forces at play:**
- Multiple memory *sources*: `MEMORY.md`, daily diaries, knowledge wiki, shared workspace
- Multiple *scopes*: `shared` (team), `user` (per-user), `session` (ephemeral)
- Must degrade gracefully: no embedding provider → keyword-only; FTS5 broken → LIKE fallback; trigram unavailable → unicode61 only
- Background maintenance must never block the conversation write path
- One SQLite file holds both conversations (irreplaceable) and memory index (rebuildable) — corruption in one must not lose the other

---

## Decision

We decompose memory into **four independent layers** with clear boundaries:

```
┌─────────────────────────────────────────────────────────────┐
│                    MemoryManager (Facade)                   │
│  search() • add_memory() • sync() • flush_memory() • status │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌───────────────┐ ┌────────────┐ ┌─────────────┐
│  Conversation │ │   Memory   │ │  Summarizer │
│    Store      │ │  Storage   │ │ (Flush Mgr) │
│ (conversation_│ │ (storage.py│ │ (summarizer.│
│  _store.py)   │ │  + vector  │ │  .py)       │
└───────────────┘ └────────────┘ └─────────────┘
        │              │              │
        │              ▼              │
        │      ┌───────────────┐      │
        │      │ VectorBackend │      │
        │      │ (vector_back- │      │
        │      │  end.py)      │      │
        │      └───────────────┘      │
        └──────────────┬──────────────┘
                       │
               ┌───────┴───────┐
               ▼               ▼
        ┌────────────┐ ┌─────────────┐
        │   SQLite   │ │  Embedding  │
        │  (WAL mode)│ │  Provider   │
        └────────────┘ └─────────────┘
```

### Layer Responsibilities

| Layer | File | Responsibility |
|-------|------|----------------|
| **ConversationStore** | `agent/memory/conversation_store.py` | Per-session message append/load, context window, turn grouping, run tracking, artifact index |
| **MemoryStorage** | `agent/memory/storage.py` | Chunk CRUD, hybrid search (vector + FTS5 + trigram + LIKE), hit tracking, index repair |
| **VectorBackend** | `agent/memory/vector_backend.py` | Pluggable embedding backends (SQLite-vec, native, remote); `VectorRecord` abstraction |
| **Summarizer / FlushManager** | `agent/memory/summarizer.py` | LLM-based conversation → daily memory distillation; threshold/overflow/daily triggers |
| **MemoryManager** | `agent/memory/manager.py` | Orchestrates above; sync from files, search API, status, dirty tracking |

### Hybrid Search Strategy (MemoryStorage)

**Three-stage fallback chain:**

1. **FTS5 unicode61** — ASCII queries only; BM25 ranking
2. **FTS5 trigram** — CJK/mixed queries + fallback when unicode61 returns empty; 3-char sliding window
3. **LIKE** — Last resort (FTS5 unavailable, trigram unavailable, or both returned empty)

**Rank normalization** — each channel's results rank-normalized to (0,1] before weighted fusion, so cosine similarity and BM25 become comparable.

**Temporal decay** — daily diary files (`memory/YYYY-MM-DD.md`, `memory/users/<id>/YYYY-MM-DD.md`) decay exponentially (half-life 30 days); `MEMORY.md` and knowledge pages are evergreen.

**Hit-popularity boost** (opt-in) — `1 + w·log₂(1+hits)` + recency term, capped at `hit_boost_max` (default 1.25).

### Two-Pass Sync (MemoryManager.sync)

```
Pass 1: Walk all files → chunk changed files → collect pending chunks (no embeddings)
Pass 2: Single embed_batch(ALL pending texts) → persist per-file
```

- Amortizes HTTP embedding cost: 100 files × 1 chunk = 1 batched call instead of 100
- **Atomicity:** never touches index until valid embeddings in hand; on embed failure, leaves index intact + `_dirty=True` for retry
- **Reconciliation:** drops stale index entries for files no longer on disk (per source root)
- **Chunker version stamp** — only when rebuilding from empty index (all chunks from current algorithm)

### Vector Backend Abstraction (vector_backend.py)

```python
class VectorBackend(Protocol):
    def upsert(records: List[VectorRecord]) -> None
    def search(query: List[float], limit: int, metadata_filter: dict) -> List[VectorMatch]
    def delete(ids: List[str]) -> None
```

- `SQLiteVectorBackend` — stores vectors in SQLite BLOB column, brute-force cosine (ok for ≤100k chunks)
- Swappable: `FaissBackend`, `QdrantBackend`, `RemoteEmbeddingBackend` without changing `MemoryStorage`
- `VectorRecord` carries metadata (`path`, `start_line`, `end_line`, `user_id`, `scope`, `source`) for filtered search

### Conversation Store (conversation_store.py)

- **One global SQLite file** (shared with memory index) — `agent_id` scopes every row
- **Sessions + Messages** tables; `agent_id` added via migration (backward compatible)
- **Runs table** — auxiliary, tracks delegated work (`parent_run_id`, `task_source`, `task_id`)
- **Artifacts table** — indexes files produced during conversation
- **Display turns** — groups tool_use + tool_result + final answer into one assistant turn for UI
- **Pruning** — age-based only (sessions not updated within N days); no size-based eviction

### Summarization Pipeline (summarizer.py)

- `MemoryFlushManager.flush_from_messages()` — called when message count crosses threshold, overflow, or daily cron
- Uses LLM to distill conversation → structured daily memory entry
- Writes to `memory/YYYY-MM-DD.md` (or per-user variant)
- Callback `context_summary_callback` injects summary into live context
- **Dream diaries** (`memory/dreams/`) — narrative reflections from Deep Dream; excluded from sync (factual content already in `MEMORY.md`)

---

## Consequences

### Positive
- **Clear separation** — conversation history ≠ semantic memory ≠ summarization
- **Graceful degradation** — every search path has a fallback; no single point of failure kills memory
- **CJK support** — trigram tokenizer + LIKE fallback handles Thai/Chinese/Japanese/Korean
- **Background repair** — integrity scan + FTS5 rebuild runs async, never blocks writes
- **Reconciliation** — deleted files actually disappear from search results
- **Testability** — each layer can be unit-tested with fakes; `VectorBackend` protocol enables fake backend
- **Scalable sync** — batched embedding cuts API calls by 10–100× for many small files

### Negative
- **More moving parts** — 5 files instead of 1 monolith
- **SQLite-only vector** — brute-force cosine doesn't scale past ~100k chunks (planned: Faiss/Qdrant backend)
- **Complex sync logic** — two-pass + reconciliation + version stamping is subtle
- **Shared DB file** — conversation history and memory index in one file; corruption handling is complex

### Risks / Mitigations
| Risk | Mitigation |
|------|------------|
| FTS5 shadow corruption silently breaks search | `_fts5_shadow_corrupt()` probe on init + background integrity scan |
| Trigram tokenizer unavailable on old SQLite | Graceful disable (`_disable_trigram_index`); LIKE fallback covers CJK |
| Embedding API failure loses sync progress | Pass 2: only writes index after *all* embeddings succeed; `_dirty` flag triggers retry |
| Chunker algorithm change invalidates old chunks | `chunker_version` meta only stamped on fresh index; `/memory status` suggests rebuild |
| Memory + conversations in one DB = single point of failure | WAL mode + busy_timeout; integrity scan reads but never moves file; manual `sqlite3 .recover` for b-tree damage |

---

## Implementation Notes

### Key Files

| File | Role |
|------|------|
| `agent/memory/manager.py` | `MemoryManager` — facade, search, sync, flush, status |
| `agent/memory/storage.py` | `MemoryStorage` — SQLite + FTS5 + trigram + vector backend + hit tracking |
| `agent/memory/vector_backend.py` | `VectorBackend` protocol, `SQLiteVectorBackend`, `VectorRecord`, `VectorMatch` |
| `agent/memory/conversation_store.py` | `ConversationStore` — sessions, messages, runs, artifacts, display turns |
| `agent/memory/summarizer.py` | `MemoryFlushManager` — LLM summarization, daily file writing |
| `agent/memory/chunker.py` | `TextChunker` — markdown-aware + plain text chunking |
| `agent/memory/embedding.py` | `EmbeddingProvider` protocol, cache |
| `agent/memory/reranker.py` | `Reranker` protocol (cross-encoder re-ranking) |
| `agent/memory/config.py` | `MemoryConfig` — all tunables (weights, thresholds, paths) |
| `agent/memory/service.py` | `MemoryService` — HTTP/JSON API for cloud client (list, content, dispatch) |

### Migration Path
1. **Phase 1 (current):** All layers in place; `MemoryManager` used by `agent_initializer` and web API
2. **Phase 2:** Pluggable `VectorBackend` — add Faiss/Qdrant for >100k chunks
3. **Phase 3:** Separate conversation DB from memory index DB (optional, for isolation)
4. **Phase 4:** Distributed vector backend (remote gRPC) for multi-node deployments

### Checklist
- [x] ConversationStore with agent_id scoping, runs, artifacts, display turns
- [x] MemoryStorage with FTS5 unicode61 + trigram + LIKE fallback chain
- [x] Two-pass sync with batched embeddings + reconciliation
- [x] VectorBackend protocol + SQLiteVectorBackend
- [x] Temporal decay (daily files) + hit-popularity boost (opt-in)
- [x] Background integrity scan + FTS5 repair
- [x] MemoryFlushManager with threshold/overflow/daily triggers
- [x] MemoryService HTTP API for cloud console
- [ ] Faiss/Qdrant VectorBackend implementations
- [ ] Integration test: sync → search → flush → search (decay + boost)
- [ ] Load test: 100k chunks, concurrent search + sync

---

## Related

- **GLOSSARY.md** entries: `MemoryManager`, `MemoryStorage`, `ConversationStore`, `VectorBackend`, `VectorRecord`, `FTS5`, `TrigramTokenizer`, `TwoPassSync`, `TemporalDecay`, `HitBoost`, `MemoryFlushManager`, `DreamDiary`
- **ADR 0001:** Multi-Agent Routing (conversation store shares DB with runs)
- **ADR 0002:** Platform Contract v1 (runs table in conversation store)
- **ADR 0004:** Skills & MCP Boundary (skills can register memory hooks)
- **Future ADR:** Pluggable Vector Backends (Faiss, Qdrant, remote)
- **Future ADR:** Separate Conversation DB vs Memory Index DB
- **External:** SQLite FTS5 documentation, trigram tokenizer spec

---

*This ADR records the architectural decision. Implementation details live in code; this document captures the **why**.*