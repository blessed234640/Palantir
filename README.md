# Palantir

A self-hosted, OpenAI-compatible LLM gateway. It exposes a single `/v1/chat/completions`
endpoint and routes requests across multiple model backends — a local model served by
[Ollama](https://ollama.com) and the Google Gemini API — handling format translation,
streaming, retries, and automatic failover between providers.

> **Status: work in progress.** Phases 1 (core gateway) and 2 (reliability) are complete.
> See the roadmap below.

## Why

Any app that talks to an LLM eventually needs the same things wrapped around it: a single
entry point, resilience when a provider fails, cost visibility, caching, and a way to swap
models without rewriting client code. Palantir is that layer — the infrastructure most
teams end up building internally — implemented from scratch with a focus on backend rigor
rather than a thin wrapper over a single provider.

Notably, it is built **without LangChain or similar frameworks**. Streaming, format
translation, retry policy, and failover are implemented directly, so the mechanics are
explicit rather than hidden behind an abstraction.

## Features

**Core gateway**

- **OpenAI-compatible API** — a drop-in `/v1/chat/completions` endpoint; any client written
  against the OpenAI SDK can point at the gateway without changes.
- **Async request forwarding** — non-blocking I/O with `httpx`, so a single process keeps
  serving other requests while a model generates.
- **Provider abstraction** — each backend lives behind a provider class exposing the same
  interface. The endpoint never knows which backend answers.
- **Streaming (SSE)** — with `stream: true`, tokens are relayed as they are generated, with
  no server-side buffering, terminated by the standard `[DONE]` marker.

**Multi-provider & reliability**

- **Bidirectional format translation** — Gemini speaks its own dialect (`contents`/`parts`,
  `model` instead of `assistant`, system prompts as a separate field). The provider
  translates requests into it and translates responses back — including **chunk-by-chunk
  translation during streaming**, so clients see one consistent format regardless of which
  backend answered.
- **Retries with exponential backoff** — transient failures are retried with a growing
  delay. Client errors (`4xx`) are not retried, since repeating a malformed request cannot
  succeed; server errors (`5xx`) and connection failures are.
- **Shared reliability layer** — retry policy lives in one place and is applied to any
  provider by composition (a higher-order wrapper around the network call), rather than
  duplicated per provider or baked into a base class.
- **Model-aware routing** — providers declare which models they serve, and the router tries
  matching providers first, falling back to the rest.
- **Failover with transparency** — if the requested model's provider is down or the model
  doesn't exist, another provider answers using its own default model, and the response
  carries a `fallback_from` field naming what was originally requested. Availability is
  preserved without silently substituting a model behind the client's back.
- **Streaming failover** — the same failover applies to streamed requests, resolved before
  the first chunk reaches the client. Once bytes are in flight an HTTP error can no longer
  be returned, so a total failure is reported as a terminal SSE chunk instead.
- **Defensive response parsing** — malformed or empty upstream responses produce a clear
  `502` rather than an unhandled exception.

## Tech stack

Python · FastAPI · httpx · Pydantic v2 · Uvicorn · Ollama · Google Gemini API

## Architecture

client ──▶ FastAPI ──▶ Router ──▶ retry wrapper ──▶ Provider ──▶ backend
endpoint (ordering, (backoff) (translation)
(validation) failover) ├─▶ Ollama (local model)
│ └─▶ Gemini API
└─ tries next provider on failure


Requests are validated by Pydantic schemas. The endpoint delegates to a router, which
orders providers by whether they serve the requested model and walks that list until one
succeeds. Each provider knows only how to talk to its own backend — building the request,
calling it, and translating the response into the common format. The retry policy wraps
that call from the outside, so reliability behavior is defined once and shared.

## Getting started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A local model pulled: `ollama pull phi4-mini`
- A Google Gemini API key (free tier available from [Google AI Studio](https://aistudio.google.com))

### Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

GEMINI_API_KEY=your_key_here


### Run

```bash
uvicorn app.main:app --reload
```

The gateway starts on `http://localhost:8000`. Interactive API docs at
`http://localhost:8000/docs`.

### Try it

Local model:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"phi4-mini","messages":[{"role":"user","content":"hello"}]}'
```

Cloud model — same endpoint, same request shape:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-2.5-flash","messages":[{"role":"user","content":"hello"}]}'
```

Streaming:

```bash
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-2.5-flash","messages":[{"role":"user","content":"tell me a short story"}],"stream":true}'
```

Failover — stop Ollama and repeat the first request. The response still returns `200`,
answered by Gemini, with `"fallback_from": "phi4-mini"` marking the substitution.

## Roadmap

- [x] **Phase 1 — Core gateway:** OpenAI-compatible endpoint, provider abstraction,
  upstream error handling, SSE streaming
- [x] **Phase 2 — Reliability:** retries with backoff, second provider with format
  translation, provider failover (including streaming), shared reliability layer,
  model-aware routing
- [ ] **Phase 3 — Caching:** exact-match cache, then semantic cache (pgvector + local
  embeddings)
- [ ] **Phase 4 — Observability:** request tracing, token/cost accounting, dashboard
- [ ] **Phase 5 — Prompt management & evals:** versioned prompts, replay, LLM-as-judge
  regression tests
- [ ] **Phase 6 — Durable agent runtime:** event-sourced, idempotent, resumable agent
  execution