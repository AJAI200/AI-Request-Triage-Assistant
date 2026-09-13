# AI Request Triage Assistant — Professional Build Plan
**Node Solutions | Stage Two Technical Challenge**
**Status: Final — ready for implementation**

> This document is the single source of truth for building this system. It's written to be handed directly to a coding assistant (or followed manually) without needing to re-derive any decisions — every choice below has already been made and justified. If you're using AI to help code this, paste the relevant section in as context before asking it to generate a file.

---

## 0. Project Summary

A tool that accepts an unstructured client request (text) and returns: a summary, a category, a priority with reason, an assigned owner, and a draft first response — replacing a manual triage process that is currently slow and inconsistent.

**Scope discipline:** This is a 48-hour prototype, not a production system. Every architectural decision below favors *working and explainable* over *scalable and sophisticated*. Where a heavier alternative exists, it is named and explicitly rejected, so nothing needs to be re-litigated mid-build.

**Final stack decision:**
| Layer | Choice |
|---|---|
| API framework | FastAPI |
| Database | **SQLite** (swapped from PostgreSQL — see §5.1) |
| ORM | SQLAlchemy, schema via `Base.metadata.create_all()` — **no Alembic, no migrations** |
| Dependency manager | uv |
| LLM | Anthropic Claude API (via a swappable client wrapper) |
| UI | FastAPI backend + a minimal server-rendered or single-page frontend (see §5.2 for the lean alternative) |
| Testing | pytest |
| Deployment | Render or Railway free tier |

---

## 1. Functional Requirements

| ID | Requirement |
|---|---|
| FR1 | Accept a free-text request as input via an API endpoint |
| FR2 | Return a 1–2 sentence summary of the request |
| FR3 | Classify into exactly one category: Sales, Support, Billing, Technical, Other |
| FR4 | Assign a priority (Low / Medium / High / Urgent) with a one-line reason |
| FR5 | Route to exactly one owner: Sales Team, Client Success, Finance, Engineering |
| FR6 | Generate a professional draft first response |
| FR7 | Present all outputs together in one clear view |
| FR8 | Correctly handle requests not present in the six provided mock examples (generalize, don't hardcode) |
| FR9 | Never crash on a malformed AI response — degrade to a visible "needs review" state |

## 2. Non-Functional Requirements

| NFR | Target | Notes |
|---|---|---|
| Performance | Response within ~3–5 seconds | Bounded by LLM latency |
| Reliability | Any AI/parsing failure returns a clean fallback, not an exception | Directly prevents the "requests get delayed/lost" failure mode described in the brief |
| Maintainability | Categories/owners stored as data (DB rows or config), never hardcoded inside prompts/logic | Adding a 6th category should be a data change, not a code change |
| Security | No real customer data used; documented that request text would need encryption-at-rest in a real deployment | Correctly scoped as "acknowledged, not solved" for a prototype |
| Scalability | Stateless request handling (no in-memory session state) | Enables horizontal scaling later without redesign, though not needed now |

---

## 3. Entity–Relationship Model

**Design principle:** model exactly the data that exists in this problem — a single-writer classification log, not a transactional multi-user system. No relationship is added unless a real business rule justifies it.

### Entities & relationships

| Relationship | Cardinality | Justification |
|---|---|---|
| `Request` → `Classification` | 1 : 1 | Every request is classified exactly once; re-classification updates the existing row rather than creating a parallel one |
| `Classification` → `Category` | Many : 1 | Many classifications reference one of five fixed categories |
| `Classification` → `Owner` | Many : 1 | Many classifications reference one of four fixed owners |
| `Request` → `ResponseDraft` | 1 : 1 | One draft per request; a human edit is a state change, not a new entity |

**Deliberately no many-to-many anywhere** — triage means committing to exactly one category and one owner per request; a tagging-style many-to-many would solve a problem this brief doesn't have.

### Schema (3NF, SQLite/PostgreSQL-compatible SQL)

```sql
CREATE TABLE category (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE           -- Sales | Support | Billing | Technical | Other
);

CREATE TABLE owner (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE           -- Sales Team | Client Success | Finance | Engineering
);

CREATE TABLE request (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_text      TEXT NOT NULL,
    channel       TEXT,                    -- email | form | chat (optional metadata)
    status        TEXT NOT NULL DEFAULT 'new',   -- new | classified | needs_review
    received_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE classification (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id        INTEGER NOT NULL UNIQUE REFERENCES request(id),
    summary           TEXT NOT NULL,
    category_id       INTEGER NOT NULL REFERENCES category(id),
    priority          TEXT NOT NULL,        -- Low | Medium | High | Urgent
    priority_reason   TEXT NOT NULL,
    owner_id          INTEGER NOT NULL REFERENCES owner(id),
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE response_draft (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id    INTEGER NOT NULL UNIQUE REFERENCES request(id),
    draft_text    TEXT NOT NULL,
    final_text    TEXT,                     -- populated if a human edits before sending
    sent_at       TIMESTAMP
);
```

**3NF justification:** no repeating groups; every non-key column depends only on its row's own primary key; category/owner names are stored once and referenced by ID. Not normalized further (e.g., splitting `priority_reason` into its own evidence table) because that level of decomposition has no benefit at this write volume.

**ACID:** the only transaction is *insert Request → insert Classification → insert ResponseDraft*, wrapped in one DB transaction. SQLite/PostgreSQL both provide full ACID guarantees on this without any custom concurrency code — there is no multi-writer contention in this system's actual usage pattern.

---

## 4. Architecture

### 4.1 Layered, single-process (not microservices)

```
┌───────────────────────────────────────────┐
│  API Layer        (FastAPI routes)         │
├───────────────────────────────────────────┤
│  Service Layer    (business orchestration) │
├───────────────────────────────────────────┤
│  Agent Layer      (AI pipeline)            │
├───────────────────────────────────────────┤
│  Data Layer       (SQLAlchemy + SQLite)    │
└───────────────────────────────────────────┘
```
Rejected: microservices (no independent scaling/deployment need exists for a single sequential pipeline).

### 4.2 Agent pipeline design — decided

**Single orchestrated pipeline, not a multi-agent framework** (no LangGraph/CrewAI/AutoGen). Every request follows the exact same fixed path — there is no dynamic branching for an autonomous agent framework to manage:

```
classify -> prioritize -> route -> draft response
```

**Implementation decision:** to keep the build lean, classify + prioritize + route are combined into **one LLM call** returning structured JSON (they're cheap, related, and safe to combine). Drafting the response is a **second, separate call**, since it benefits from seeing the finalized classification first. This is expressed in code as a single `TriageAgent` module (not four separate agent classes) — the earlier idea of four independent agent classes was reconsidered as unnecessary ceremony for this scope; one well-structured module with two LLM calls achieves the same separation of concerns with less code to maintain.

```
[TriageAgent.classify_and_route(text)] -> {summary, category, priority, priority_reason, owner}
[TriageAgent.draft_response(text, classification)] -> {draft_response}
```

### 4.3 End-to-end data flow

```
POST /triage {text}
     |
     v
routes/triage_routes.py
     |
     v
services/triage_service.py
     |
     +--> INSERT Request (status='new')
     |
     v
agents/triage_agent.py
     |
     +--> classify_and_route()  --> client/llm_client.py --> LLM API
     |        (validated via utils/validators.py + utils/json_parser.py)
     |
     +-- success --> draft_response() --> LLM API
     |                  |
     |                  +-- success --> INSERT Classification, INSERT ResponseDraft
     |                  |              UPDATE Request.status = 'classified'
     |                  +-- failure --> UPDATE Request.status = 'needs_review'
     |
     +-- failure --> UPDATE Request.status = 'needs_review'
     |
     v
routes/triage_routes.py -> returns JSON result to caller
```

### 4.4 DTOs — separating "what the API looks like" from "what the database looks like"

**Pattern used: Data Transfer Object (DTO).** Two files, one job each:

- `dtos/request_dto.py` — defines exactly what shape of data the API will *accept*. This is the validation boundary: if the input doesn't match, FastAPI rejects it before any business logic runs.
- `dtos/response_dto.py` — defines exactly what shape of data the API will *return*. This decouples the outward-facing contract from the internal SQLAlchemy models, so changing a DB column name later doesn't silently change your API's public shape (and vice versa).

This is a genuinely useful pattern here, not an unnecessary one, because FastAPI's own tooling (Pydantic) makes it nearly free — you get input validation, auto-generated OpenAPI docs, and clear typed contracts for a coding assistant to build against, all from writing two small classes. It's the one pattern in this plan that's *cheaper to use than to skip*.

```python
# src/dtos/request_dto.py
from pydantic import BaseModel, Field

class TriageRequestDTO(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
```

```python
# src/dtos/response_dto.py
from pydantic import BaseModel
from typing import Optional

class TriageResponseDTO(BaseModel):
    id: int
    status: str                        # "classified" | "needs_review"
    summary: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    priority_reason: Optional[str] = None
    owner: Optional[str] = None
    draft_response: Optional[str] = None
    message: Optional[str] = None      # populated only when status == "needs_review"
```

`routes/triage_routes.py` then simply declares these as its input/output types — FastAPI handles validation and serialization automatically:

```python
# src/routes/triage_routes.py
from fastapi import APIRouter
from src.dtos.request_dto import TriageRequestDTO
from src.dtos.response_dto import TriageResponseDTO
from src.services.triage_service import run_triage

router = APIRouter()

@router.post("/triage", response_model=TriageResponseDTO)
async def create_triage(payload: TriageRequestDTO):
    result = await run_triage(payload.text)
    return TriageResponseDTO(**result)
```

### 4.5 Design-pattern philosophy for this build

The guiding rule: **use a pattern only where it removes real duplication or ambiguity — never to demonstrate that a pattern was used.** Patterns applied here, each with a one-line reason:

| Pattern | Where | Why it earns its place |
|---|---|---|
| **DTO** | `dtos/` | Separates API contract from DB schema; nearly free via Pydantic (see 4.4) |
| **Dependency Injection** | FastAPI route functions receive `payload: TriageRequestDTO` and (if needed later) a DB session via `Depends()` | Built into FastAPI already — using it is the path of least code, not extra ceremony |
| **Single Responsibility** | Each module (`agents/`, `services/`, `routes/`, `utils/`) does exactly one job | This is a principle, not a formal "pattern," but it's the one doing the most work to keep the code explainable |
| **Strategy (implicit, not built)** | `llm_client.py` is the only place that knows which LLM provider is in use | Not a formal Strategy class hierarchy — just one function behind one import path, so swapping providers later touches one file. Building an actual `LLMProviderStrategy` interface with multiple implementations would be solving a problem ("we need to swap providers at runtime") that doesn't exist yet |

**Explicitly rejected for this scope:** Factory classes for object creation (nothing here is complex enough to need a factory — direct instantiation is clearer), Observer/event-driven patterns (no multiple independent listeners exist), Repository pattern (see §5.5 — reconsidered as unnecessary), and any generic "manager" or "handler" abstraction layer that doesn't map to a real, named responsibility. If a coding assistant suggests one of these, the answer is: only if it removes duplication that actually exists in the code at that point — not preemptively.

---

## 5. Key Decisions & Rationale (so a coding assistant doesn't reintroduce rejected options)

### 5.1 SQLite instead of PostgreSQL
Nothing in this system requires a networked, multi-user database — it's single-writer, low-volume, demoed by one person. SQLite gives identical SQLAlchemy code (swapping to PostgreSQL later is a one-line `DATABASE_URL` change) with zero setup and no external service to provision or keep alive.

### 5.2 FastAPI kept (not Streamlit) — with a documented lean fallback
FastAPI was kept because the brief scores "Functionality... main workflow works reliably from input to output" and free OpenAPI docs make the API inspectable in the video with no extra effort. **If time runs short, the fallback is a Streamlit single-file app calling the same `services/` and `agents/` modules directly** — those layers don't change either way, only the outer UI/routing layer does.

### 5.3 No Alembic / no migrations folder
`Base.metadata.create_all()` on startup is sufficient because there is no production data that must be preserved across schema changes. If a column needs to change mid-build: drop the table, edit the model, restart. Alembic is deferred to a genuine "next steps" item, not built now.

### 5.4 One `TriageAgent` module, not four separate agent classes, not a multi-agent framework
Originally planned as four separate agent classes (`ClassifierAgent`, `PriorityAgent`, `RoutingAgent`, `ResponderAgent`) for modularity. Reconsidered: since three of the four share one LLM call anyway, splitting them into separate classes added file count without adding real separation of concerns. Two functions in one module (`classify_and_route`, `draft_response`) achieve the same testability with less code.

### 5.5 No repository layer
Originally planned (`repositories/request_repository.py` etc.) for ORM-swap flexibility. Reconsidered as unnecessary for three tables with no test-mocking requirement severe enough to need it — `services/triage_service.py` talks to SQLAlchemy directly. This can be reintroduced later with no impact on `routes/` or `agents/`.

### 5.6 Rejected outright (do not build)
- Microservices — no independent scaling/deployment need
- Vector DB / RAG over past tickets — no evidence classification quality needs historical context yet
- Payment processing / concurrency queues — not present in the actual problem
- Multi-agent framework with autonomous branching — control flow is fixed, not decided dynamically

---

## 6. Folder Structure (final)

```
project-root/
|-- src/
|   |-- agents/
|   |   |-- __init__.py
|   |   |-- triage_agent.py          # classify_and_route(), draft_response()
|   |   |-- llm_client.py            # thin wrapper around Anthropic SDK
|   |   |-- prompts.py               # all prompt templates, kept together for easy tuning
|   |
|   |-- dtos/
|   |   |-- __init__.py
|   |   |-- request_dto.py           # what the API accepts (input shape + validation)
|   |   |-- response_dto.py          # what the API returns (output shape, both success and fallback)
|   |
|   |-- models/
|   |   |-- __init__.py
|   |   |-- base.py                  # SQLAlchemy Base + engine + SessionLocal
|   |   |-- category.py
|   |   |-- owner.py
|   |   |-- request.py
|   |   |-- classification.py
|   |   |-- response_draft.py
|   |
|   |-- routes/
|   |   |-- triage_routes.py         # POST /triage, GET /triage/{id}, GET /triage
|   |
|   |-- services/
|   |   |-- triage_service.py        # orchestrates: DB writes + calls to agents/triage_agent.py
|   |
|   |-- utils/
|   |   |-- validators.py            # enum checks: category/priority/owner allow-lists
|   |   |-- json_parser.py           # safe LLM-JSON parsing, raises on malformed output
|   |
|   |-- database.py                  # init_db(), seed_lookup_tables()
|   |-- settings.py                  # env config: LLM_API_KEY, DATABASE_URL, model name
|   |-- main.py                      # FastAPI app, startup hook, route registration
|   |-- __init__.py
|
|-- test/
|   |-- fixtures/
|   |   |-- mock_requests.py         # the six mock requests from the brief
|   |-- test_triage_agent.py         # unit test: prompt -> valid structured output
|   |-- test_triage_service.py       # integration test: full pipeline, in-memory SQLite
|   |-- test_triage_routes.py        # API-level test via FastAPI TestClient
|
|-- .env
|-- .env.example
|-- pyproject.toml                   # uv-managed
|-- uv.lock
|-- README.md
```

---

## 7. API Contract

### `POST /triage`
**Request body:**
```json
{ "text": "The client portal has been unavailable since this morning..." }
```

**Response (success, 200):**
```json
{
  "id": 12,
  "status": "classified",
  "summary": "Client portal outage blocking staff access to customer records.",
  "category": "Technical",
  "priority": "Urgent",
  "priority_reason": "Active outage with explicit request for immediate help.",
  "owner": "Engineering",
  "draft_response": "We're sorry for the disruption -- we're escalating this immediately..."
}
```

**Response (fallback, 200 -- deliberately not a 500, since this is an expected state, not a bug):**
```json
{
  "id": 13,
  "status": "needs_review",
  "message": "Could not automatically classify this request. Please review manually."
}
```

### `GET /triage/{id}`
Returns the stored result for a previously submitted request (same shape as above).

### `GET /triage`
Returns a list of recent requests with their status, for a simple dashboard view.

---

## 8. Core Logic Reference

### 8.1 Database bootstrap (no migrations)
```python
# src/database.py
from src.models.base import Base, engine, SessionLocal
from src.models.category import Category
from src.models.owner import Owner

def init_db():
    Base.metadata.create_all(bind=engine)
    seed_lookup_tables()

def seed_lookup_tables():
    with SessionLocal() as session:
        if session.query(Category).count() == 0:
            session.add_all([Category(name=c) for c in
                ["Sales", "Support", "Billing", "Technical", "Other"]])
        if session.query(Owner).count() == 0:
            session.add_all([Owner(name=o) for o in
                ["Sales Team", "Client Success", "Finance", "Engineering"]])
        session.commit()
```

### 8.2 Agent module
```python
# src/agents/triage_agent.py
from src.agents.llm_client import call_llm
from src.agents.prompts import CLASSIFY_ROUTE_PROMPT, DRAFT_RESPONSE_PROMPT
from src.utils.json_parser import parse_llm_json
from src.utils.validators import validate_classification

async def classify_and_route(raw_text: str) -> dict:
    output = await call_llm(CLASSIFY_ROUTE_PROMPT, raw_text)
    result = parse_llm_json(output)      # raises JSONParseError on malformed output
    validate_classification(result)      # raises ValidationError on out-of-range values
    return result

async def draft_response(raw_text: str, classification: dict) -> dict:
    output = await call_llm(DRAFT_RESPONSE_PROMPT, raw_text, context=classification)
    return parse_llm_json(output)
```

### 8.3 Service orchestration
```python
# src/services/triage_service.py
from src.agents.triage_agent import classify_and_route, draft_response
from src.models.request import Request
from src.models.classification import Classification
from src.models.response_draft import ResponseDraft
from src.models.base import SessionLocal
from src.utils.json_parser import JSONParseError
from src.utils.validators import ValidationError

async def run_triage(raw_text: str) -> dict:
    with SessionLocal() as session:
        req = Request(raw_text=raw_text, status="new")
        session.add(req)
        session.commit()
        session.refresh(req)

        try:
            classification = await classify_and_route(raw_text)
            draft = await draft_response(raw_text, classification)
        except (JSONParseError, ValidationError):
            req.status = "needs_review"
            session.commit()
            return {"id": req.id, "status": "needs_review",
                    "message": "Could not automatically classify this request. Please review manually."}

        session.add(Classification(
            request_id=req.id,
            summary=classification["summary"],
            category_id=lookup_category_id(session, classification["category"]),
            priority=classification["priority"],
            priority_reason=classification["priority_reason"],
            owner_id=lookup_owner_id(session, classification["owner"]),
        ))
        session.add(ResponseDraft(request_id=req.id, draft_text=draft["draft_response"]))
        req.status = "classified"
        session.commit()

        return {
            "id": req.id,
            "status": "classified",
            **classification,
            "draft_response": draft["draft_response"],
        }
```

### 8.4 Prompts
```python
# src/agents/prompts.py

CLASSIFY_ROUTE_PROMPT = """You are a request-triage assistant for a professional services company.
Given a client request, return ONLY valid JSON with these exact keys:

{
  "summary": "<1-2 sentence summary>",
  "category": "<one of: Sales, Support, Billing, Technical, Other>",
  "priority": "<one of: Low, Medium, High, Urgent>",
  "priority_reason": "<one sentence justification>",
  "owner": "<one of: Sales Team, Client Success, Finance, Engineering>"
}

Guidance:
- Urgent = active harm, outage, security/data exposure, or explicit "immediately/ASAP" language.
- High = has a real deadline or financial/operational risk, but not actively breaking right now.
- Medium = genuine interest or need, no explicit deadline.
- Low = ideas/suggestions, no time pressure, explicitly "no deadline."
- Data exposure or privacy incidents are ALWAYS at least Urgent, regardless of tone.
- Billing/invoice/payment issues -> Finance. Portal/bugs/security -> Engineering.
  New business/pricing inquiries -> Sales Team. Everything else client-relationship-related -> Client Success.
Return ONLY the JSON object, no other text."""

DRAFT_RESPONSE_PROMPT = """You are drafting a first-response email for a professional services company.
Given the original client request and its classification, write a short (2-4 sentence),
professional, empathetic draft reply a team member can review and send.
Return ONLY valid JSON: {"draft_response": "<the drafted reply>"}"""
```

### 8.5 Validation
```python
# src/utils/validators.py
ALLOWED_CATEGORIES = {"Sales", "Support", "Billing", "Technical", "Other"}
ALLOWED_PRIORITIES = {"Low", "Medium", "High", "Urgent"}
ALLOWED_OWNERS = {"Sales Team", "Client Success", "Finance", "Engineering"}

class ValidationError(Exception):
    pass

def validate_classification(result: dict):
    if result.get("category") not in ALLOWED_CATEGORIES:
        raise ValidationError(f"Invalid category: {result.get('category')}")
    if result.get("priority") not in ALLOWED_PRIORITIES:
        raise ValidationError(f"Invalid priority: {result.get('priority')}")
    if result.get("owner") not in ALLOWED_OWNERS:
        raise ValidationError(f"Invalid owner: {result.get('owner')}")
    if not result.get("summary"):
        raise ValidationError("Missing summary")
```

---

## 9. Edge Cases (must be handled, not just documented)

| Edge case | Handling |
|---|---|
| Empty input | Reject at the route level with a 400, before calling the LLM |
| Malformed LLM JSON | `json_parser.py` raises `JSONParseError` -> caught in `triage_service.py` -> `needs_review` |
| LLM returns an out-of-allow-list value | `validators.py` raises `ValidationError` -> same fallback path |
| Ambiguous request (fits two categories) | Not force-resolved; `priority_reason` is surfaced so a human can override -- deliberate design choice |
| Long pasted email thread | Truncate `raw_text` to a safe character limit before the LLM call |
| Concurrent submissions | SQLite/PostgreSQL transaction isolation handles this correctly at this scale; no custom locking |
| Request not among the six mock examples | Must be handled correctly -- this is FR8 and should be explicitly tested |

---

## 10. Testing Plan

```python
# test/fixtures/mock_requests.py
MOCK_REQUESTS = [
    "Our team has 40 employees entering the same customer details into three systems...",
    "The client portal has been unavailable since this morning...",
    "Invoice NS-1048 appears to include the same implementation charge twice...",
    "Can you add dark mode and change the dashboard font?...",
    "We accidentally uploaded a spreadsheet containing customer contact information...",
    "I saw your company online and am interested in a custom AI reporting system...",
]
```

- `test_triage_agent.py` -- run each mock request through `classify_and_route()`, assert the output passes `validate_classification()`.
- `test_triage_service.py` -- run the full pipeline against an in-memory SQLite DB, assert rows are created correctly for each mock request, including request 05 landing as `Urgent`.
- `test_triage_routes.py` -- hit `POST /triage` via FastAPI's `TestClient`, assert 200 responses and correct JSON shape.
- **Also test at least one request not in the mock set**, to demonstrate FR8 generalization -- this is a differentiator, not just a formality.

---

## 11. Deployment Plan

1. Push repo to GitHub.
2. Deploy on **Render** (or Railway) free tier -- connect the repo, set build command (`uv sync`) and start command (`uvicorn src.main:app --host 0.0.0.0 --port $PORT`).
3. Set environment variables (`LLM_API_KEY`, `DATABASE_URL=sqlite:///./triage.db`) in the platform's dashboard -- never commit `.env`.
4. Optional GitHub Action smoke test before merge:

```yaml
# .github/workflows/test.yml
name: smoke-test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install uv && uv sync
      - run: uv run pytest test/
```

5. Monitoring: `Request.status` values (`new / classified / needs_review`) serve as the monitoring signal -- no external observability tooling needed at this scale.

---

## 12. Build Order Checklist

- [ ] `models/` -- define all 5 tables, `database.py` with `init_db()` + seeding
- [ ] `dtos/request_dto.py`, `dtos/response_dto.py` -- Pydantic input/output contracts
- [ ] `agents/llm_client.py` -- LLM API wrapper
- [ ] `agents/prompts.py` -- both prompts
- [ ] `agents/triage_agent.py` -- `classify_and_route()`, `draft_response()`
- [ ] `utils/validators.py`, `utils/json_parser.py`
- [ ] `services/triage_service.py` -- full orchestration + DB writes
- [ ] `routes/triage_routes.py` -- all three endpoints, typed with the DTOs
- [ ] `main.py` -- FastAPI app, startup hook calling `init_db()`
- [ ] Run all six mock requests manually, confirm sensible output for each
- [ ] Test one request NOT in the mock set (FR8)
- [ ] Test empty input, malformed-response simulation, long input
- [ ] `test/` -- all three test files passing
- [ ] Minimal frontend (form + results view), or confirm OpenAPI docs are sufficient for demo
- [ ] Deploy to Render/Railway, verify the live URL works end-to-end
- [ ] Record 5-8 minute video: live demo (3+ requests incl. #05) -> architecture walkthrough -> decisions/trade-offs -> what you'd improve next

---

## 13. Trade-offs to State Explicitly in the Video

| Decision | One-line reasoning to say out loud |
|---|---|
| SQLite, not PostgreSQL | No multi-user concurrency exists in this problem |
| No Alembic | No production data to preserve across schema changes yet |
| One `TriageAgent` module, two LLM calls, not 4 separate agent classes or a multi-agent framework | Control flow is fixed and sequential -- no dynamic agent decisions to orchestrate |
| No repository layer | Three tables, no ORM-swap requirement severe enough to justify the extra layer |
| `needs_review` fallback, not a retry queue | Simple, visible, honest failure handling appropriate to this scale |
| FastAPI kept over Streamlit | Matches the brief's "workflow" framing and gives free API docs for the demo |
| DTOs used, but no Factory/Repository/Observer patterns | Only added patterns that remove real duplication (DTO via Pydantic is nearly free); rejected patterns that would solve problems this system doesn't have |