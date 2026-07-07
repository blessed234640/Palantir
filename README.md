# Palantir
 
A self-hosted, OpenAI-compatible LLM gateway. It exposes a single `/v1/chat/completions`
endpoint and routes requests to one or more model backends — starting with a local model
served by [Ollama](https://ollama.com) — while handling streaming and upstream failures,
and (in later phases) caching, observability, and reliable agent execution.
 
> **Status: work in progress.** Phase 1 — a working streaming passthrough gateway — is
> complete. See the [roadmap](#roadmap) below.
 
## Why
 
Any app that talks to an LLM eventually needs the same things wrapped around it: a single
entry point, resilience when a provider fails, cost visibility, caching, and a way to swap
models without rewriting client code. Palantir is that layer — the infrastructure most
teams end up building internally — implemented from scratch with a focus on backend rigor
rather than a thin wrapper over a single provider.
 
## Features (Phase 1)
 
- **OpenAI-compatible API** — a drop-in `/v1/chat/completions` endpoint; any client written
  against the OpenAI SDK can point at the gateway without changes.
- **Async request forwarding** — non-blocking I/O with `httpx`, so a single process keeps
  serving other requests while a model generates.
- **Provider abstraction** — the backend call lives in a dedicated provider class, not in
  the endpoint. The endpoint calls `provider.chat()` without knowing which backend answers,
  so adding a new backend means implementing the same methods.
- **Streaming (SSE)** — with `stream: true`, tokens are relayed to the client as they are
  generated, chunk by chunk, with no server-side buffering.
- **Upstream error handling** — distinguishes "backend returned an error" (`502`) from
  "backend unreachable" (`503`) and returns a clear response instead of a stack trace.
- **Local model backend** — runs a local model (e.g. `phi4-mini`) via Ollama; no API keys
  required to run.
## Tech stack
 
Python · FastAPI · httpx · Pydantic v2 · Uvicorn · Ollama
 
## Architecture
 
```
client ──▶ FastAPI endpoint ──▶ Provider ──▶ Ollama (/v1/chat/completions)
             (validation)        (httpx,        (local model)
                                  error handling,
                                  streaming)
```
 
Incoming requests are validated by Pydantic schemas. The endpoint stays thin and delegates
the actual backend call to a provider object — a design chosen so that adding new backends
(cloud APIs, etc.) is a matter of implementing the same interface.
 
## Getting started
 
### Prerequisites
 
- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A local model pulled:
```bash
  ollama pull phi4-mini
```
 
### Setup
 
```bash
# clone the repo, then:
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
 
### Run
 
```bash
uvicorn app.main:app --reload
```
 
The gateway starts on `http://localhost:8000`. Interactive API docs (Swagger UI) are at
`http://localhost:8000/docs`.
 
### Try it
 
Non-streaming:
 
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"phi4-mini","messages":[{"role":"user","content":"hello"}]}'
```
 
Streaming (tokens arrive incrementally):
 
```bash
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"phi4-mini","messages":[{"role":"user","content":"tell me a short story"}],"stream":true}'
```
 
## Roadmap
 
- [x] **Phase 1 — Core gateway:** OpenAI-compatible endpoint, provider abstraction,
  upstream error handling, SSE streaming
- [ ] **Phase 2 — Reliability:** retries with backoff, timeouts, provider fallback,
  circuit breaker, rate limiting
- [ ] **Phase 3 — Caching:** exact-match cache, then semantic cache (pgvector + local
  embeddings)
- [ ] **Phase 4 — Observability:** request tracing, token/cost accounting, dashboard
- [ ] **Phase 5 — Prompt management & evals:** versioned prompts, replay, LLM-as-judge
  regression tests
- [ ] **Phase 6 — Durable agent runtime:** event-sourced, idempotent, resumable agent
  execution
 