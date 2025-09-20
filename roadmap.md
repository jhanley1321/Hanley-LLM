# RAG‑First Chat Assistant — Roadmap

This roadmap captures the high‑level plan, concrete tech stack, and the first milestone needed to demo **“Local LLM + Infinite Conversation”** using RAG, plus a concise backlog.

---

## 1) High‑Level Plan

### Phase 1 — RAG Core (Infinite Conversation)
- **Infinite conversation via RAG**: Persist conversation turns to a vector store; retrieve relevant prior turns so replies aren’t limited by the model’s native context window.
- **CAG / “Think deeper” mode**: A user toggle that temporarily expands retrieval depth (more chunks, broader window) and allocates a larger reasoning budget for deeper answers.
- **Context cleanup controls**: Allow inclusion/exclusion of topics, sources, or time ranges; quick “mute topic” and “pin topic.”
- **Multi‑chat RAG**: Retrieval across a user’s prior chats, not just the current thread.
- **Multi‑project workspaces**: Per‑project corpora; switch or combine scopes on demand.
- **Automatic topic splitting & archival**: Detect topic shifts; segment long threads; keep provenance.
- **Citations & provenance**: Inline citations with page/section or prior‑turn IDs and hoverable snippets.
- **Guardrails & cost controls**: Rate limiting, quotas, backpressure; prompt‑injection filtering; optional PII redaction.

### Phase 2 — Multi‑LLM (after RAG foundation)
- **Manual model switching mid‑conversation**: Continue the same thread with another model using the same retrieved context.
- **Basic router (later)**: Heuristics to suggest/auto‑pick a model based on task type, cost, and latency.
- **Shared handoff**: Preserve conversation state and citations when switching engines.

### Phase 3 — UX & Platform
- **Frontend**: Start with Streamlit; migrate to **Next.js** once validated.
- **Auth & tenancy**: Clerk for authentication; per‑user/project isolation.
- **Billing/usage**: Tiered quotas; metered tokens; usage dashboard.
- **Admin & observability**: Traces, logs, cost per tenant, retrieval quality metrics.

### Phase 4 — Connectors & Light Agents (post‑MVP)
- **Connectors**: Files (PDF/DOCX/MD/TXT), URLs, cloud drives.
- **Light agents**: Summarize, compare docs, generate briefs orchestrated on top of RAG.

---

## 2) Tech Stack (Short‑term vs Long‑term)

**Frontend**
- **Short‑term:** Streamlit (fast demo, minimal code)
- **Long‑term:** Next.js + Tailwind; keep API contracts stable to swap frontends later

**Backend**
- **Framework:** FastAPI (with Uvicorn)
- **Data/ORM:** SQLAlchemy + Alembic
- **Queues/Cache:** Redis (optional at M1), Celery or RQ later
- **Logging:** structlog or loguru
- **Testing:** pytest + httpx

**LLMs**
- **Local (prototype):** Ollama in Docker serving `llama3.1:8b` or `mistral:7b` (quantized variants OK)
- **Cloud (later):** Azure OpenAI or equivalent as optional higher‑quality engines

**Embeddings & Retrieval**
- **Embeddings (local):** Ollama `nomic-embed-text` OR sentence‑transformers (`bge-small-en-v1.5` / `bge-base-en-v1.5`)
- **Vector store:** PostgreSQL + pgvector (preferred) OR Chroma (fastest to ship)
- **Hybrid search (optional):** pg_trgm/BM25 for lexical recall; CrossEncoder/LLM rerank
- **Reranking (optional but recommended):** sentence‑transformers CrossEncoder `cross-encoder/ms-marco-MiniLM-L-6-v2` or `jinaai/jina-reranker-v2-base-multilingual`

**Storage & Data**
- **Blob storage:** Azure Blob for raw files/artifacts (when external docs are added)
- **Relational DB:** PostgreSQL (users, projects, docs, chunks, messages, usage)

**Auth & Tenancy**
- **Auth:** Clerk
- **Isolation:** Per‑tenant row‑level security and scoped indices

**Observability & Safety**
- **Metrics/logs:** OpenTelemetry + structured logs; dashboards for cost/retrieval quality
- **Safety:** Prompt‑injection filtering, MIME/virus checks on upload, optional PII redaction

---

## 3) Milestone 1 — “Local LLM + Infinite Conversation” Demo

**Objective**  
Deliver a demo where a user chats with a local LLM via a web UI, with effectively unlimited conversation length using RAG.

**Deliverables**
- Streamlit UI (single page): input box, streamed responses, toggle for **Think Deeper**
- FastAPI backend: `/chat` (generation), `/ingest` (store turns), `/retrieve` (top‑k), `/think_deeper` (depth toggle)
- Local LLM (Ollama) in Docker
- Vector store with conversation turns persisted and searchable
- Inline citations showing which prior turns were used

**Scope Boundaries (explicit)**
- Single model only (local) for this milestone
- No external document ingestion yet (chat history only)
- No billing; minimal auth (optional Clerk sign‑in)

**Start‑to‑Finish Steps**
1. **Environment & Containers**  
   - Docker Compose services: `api` (FastAPI), `ollama`, `vector` (Chroma or Postgres+pgvector), optional `redis`, `ui` (Streamlit)  
   - Pull models with Ollama on container start (`llama3.1:8b` or `mistral:7b` for responses; `nomic-embed-text` or `bge-m3` for embeddings)
2. **Data model**  
   - Tables: `users`, `projects`, `conversations`, `messages`, `message_chunks` (embeddings), `usage`
3. **Ingestion (chat memory)**  
   - On each user/assistant message: normalize, chunk (~300–500 tokens, 20% overlap), embed, store with metadata (speaker, timestamp, convo_id)
4. **Retrieval**  
   - For a new prompt: vector search top‑k prior turns; optional lexical recall; optional rerank; pack context with strict token budget
5. **Generation**  
   - System prompt instructing grounding in retrieved context; stream tokens back to UI; add inline citations `[turn #42]`
6. **Think Deeper (CAG)**  
   - When enabled: raise top‑k, broaden time window, allow larger context budget; log the mode for cost tracking
7. **UI**  
   - Streamlit front end calling FastAPI; show conversation, citations, and a simple “Think Deeper” toggle
8. **Guardrails & Limits**  
   - Per‑IP/user rate limit; max tokens per reply; global kill switch; logging for tokens in/out
9. **Observability**  
   - Log retrieval hit rate, average ctx tokens, null‑answer rate; simple admin page (text/JSON) is enough

**Minimal API surface (M1)**
- `POST /chat` → `{conversation_id, message, think_deeper?: bool}` → SSE stream; backend retrieves prior turns and generates answer with citations
- `POST /ingest` → internal ingestion of normalized turns + embeddings
- `GET /conversations/:id/messages` → fetch history for UI replay
- `GET /messages/:id/retrievals` → debug which turns were cited

**Retrieval recipe (M1)**
1. Embed the incoming user message.  
2. Vector search: top‑k prior turns in the same conversation (k=12 default; k=24 when **Think Deeper** is on).  
3. Optional lexical recall over last N turns (BM25/pg_trgm) and union with vector hits.  
4. Optional CrossEncoder rerank to top 6–10.  
5. Pack context under a fixed budget (e.g., 2–3k tokens), dedupe by turn, and generate with the local LLM.  
6. Return citations `[turn #]` inline.

**Acceptance Criteria**
- A 200+ turn conversation remains coherent by retrieving relevant prior context
- Toggling **Think Deeper** measurably increases retrieved context and improves answers in a test script
- Citations link to specific prior turns used for each answer

**Risks & Mitigations**
- *Retrieval drift on long chats*: add reranking; cap per‑topic diversity  
- *Latency when “Think Deeper” is on*: cache recent embeddings; parallelize retrieval  
- *Cost creep (if cloud embeddings used)*: prefer local embeddings initially; batch operations

**Effort (rough)**
- 20–35 hours for a functional demo, depending on prior familiarity with pgvector/Ollama/Streamlit

---

## 4) Milestone 1: Concrete Library Choices (local‑first)

**Core runtime**  
Python 3.11+; **FastAPI**, **Uvicorn**, **Pydantic**; **SQLAlchemy** + **Alembic**; **psycopg** + **pgvector** (or **chromadb** client if you keep Chroma); **Redis** (optional); **structlog** or **loguru**.

**LLM inference (local)**  
**Ollama** container serving `llama3.1:8b` or `mistral:7b` (quantized variants for CPU‑only dev).

**Embeddings (local)**  
Option A: **Ollama** `nomic-embed-text`.  
Option B: **sentence‑transformers** with `bge-small-en-v1.5` or `bge-base-en-v1.5`.

**Reranking (local, optional but recommended)**  
**sentence‑transformers CrossEncoder**: `cross-encoder/ms-marco-MiniLM-L-6-v2` or `jinaai/jina-reranker-v2-base-multilingual` (CPU‑friendly).

**Chunking & tokenization**  
**tiktoken** or **tokenizers**; target 300–500 token chunks with 15–20% overlap.

**Frontend (temporary)**  
**Streamlit** calling FastAPI; stream via SSE (`sse-starlette` or `StreamingResponse`).

**Rate limiting & safety**  
**slowapi** or **starlette-limiter** (Redis backend). Prompt‑injection filtering on retrieved text.

**Testing**  
**pytest** + **httpx**; fixtures with **faker**.

---

## 5) Milestone 1: Actionable Steps (checklist)

**Step 1 — Repo hygiene & config**  
- Add `.env.example` with keys for DB, Redis, Ollama host  
- Pin versions in `requirements.txt`  
- Create `docker-compose.yml` with services: `api`, `ollama`, `vector` (Chroma or Postgres), `ui`, optional `redis`  
- **Done when:** containers build and start; `/health` returns 200

**Step 2 — Data layer**  
- If **Chroma**: create collection `chat_turns` with metadata `{conversation_id, turn_id, role, ts}`  
- If **pgvector**: create tables and an HNSW index on `message_chunks.embedding`  
- **Done when:** you can upsert and query a dummy embedding

**Step 3 — Embeddings + chunker**  
- Implement `embed_text()` (Ollama `nomic-embed-text` or BGE)  
- Implement `chunk_text()` (300–500 tokens, overlap 15–20%) tagging `turn_id`  
- **Done when:** a message is chunked, embedded, and stored with metadata

**Step 4 — Retrieval**  
- Implement `retrieve_prior_turns(conversation_id, query_embedding, k)` with optional rerank  
- **Done when:** given a query, you get ordered turn IDs + snippets

**Step 5 — Generation + citations**  
- FastAPI `POST /chat`: ingest, retrieve, pack, generate (stream), return `[turn #]` citations  
- **Done when:** streamed output + citations render in UI

**Step 6 — Think Deeper (CAG)**  
- Add `think_deeper` flag to `/chat` that raises k and context budget  
- **Done when:** toggling clearly changes retrieval and answer depth

**Step 7 — UI wiring (Streamlit)**  
- Minimal page: input, **Think Deeper** toggle, message list w/ hoverable citations  
- **Done when:** end‑to‑end chat works in browser

**Step 8 — Limits & safety**  
- `slowapi` rate limits per user/IP; global kill switch  
- Cap max output tokens per reply; log tokens in/out  
- **Done when:** rate limits trigger under spam; logs show usage

**Step 9 — Sanity tests**  
- Pytest: chunking, embeddings, retrieval ordering, `/chat` happy path  
- Script a 200‑turn conversation and verify coherence + citations  
- **Done when:** tests pass; long chat stays grounded

---

## 6) Feature Backlog (later phases)
- External document RAG (files, URLs) with citations  
- Multi‑project workspaces; cross‑project queries  
- Manual model switching mid‑chat; later, a simple router  
- Advanced topic splitting & archival UI  
- Next.js front end with saved prompts, shareable links, and diff views  
- Usage dashboard and plan quotas
