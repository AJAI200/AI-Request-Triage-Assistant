# AI Request Triage Assistant — Architecture & Technical Flow Specification

## 🏛️ System Architecture Overview

The **AI Request Triage Assistant** is engineered as a decoupled, multi-tiered enterprise application designed to process unstructured business requests, categorize intent, assign priority scores, route to owner teams, and generate tailored initial draft responses.

```mermaid
graph TD
    Client[React 18 / Vite / GSAP SPA] -->|HTTPS REST API| Router[FastAPI Router Layer]
    Router -->|Header Inspection| Auth[Auth Middleware & HMAC Validation]
    Auth -->|DTO Schema Validation| DTO[Pydantic Request DTO]
    DTO -->|Service Execution| Service[Triage Service Layer]
    
    Service -->|LLM Prompting| Agent[Triage Agent Pipeline]
    Agent -->|SDK/REST Call| LLMClient[LLM Client & Exponential Retry]
    LLMClient -->|API Call| Gemini[Google Gemini API]
    
    Service -->|JSON Parsing & Validation| Parser[JSON Parser & Lookups]
    Service -->|Async ORM Operations| Repo[Async SQLite Repository Layer]
    Repo -->|Async Driver| DB[(SQLite Database)]
```

---

## ⏱️ Detailed Request Execution & Exception Flow

The sequence diagram below details the two-tier error boundary architecture, showing how domain/LLM errors trigger graceful degradation (`needs_review`) while system errors trigger DB error logging.

### PlantUML Flow Diagram (`architecture_sequence.puml`)

```plantuml
@startuml Architecture_Flow
!theme plain
autonumber
actor Client as "React Client / API Consumer"
participant Router as "FastAPI Route Handler\n(src/routes/triage_routes.py)"
participant Auth as "Auth Middleware\n(src/middleware/auth_middleware.py)"
participant Service as "Triage Service\n(src/services/triage_service.py)"
participant Agent as "Triage Agent\n(src/agents/triage_agent.py)"
participant LLM as "LLM Client Wrapper\n(src/agents/llm_client.py)"
participant Gemini as "Google Gemini API"
participant Repo as "Triage Repository\n(src/repositories/triage_repository.py)"
database DB as "SQLite Database\n(triage.db)"

Client -> Router: POST /triage { "text": "Invoice NS-1048 duplicate..." }
activate Router

Router -> Auth: Validate JWT Bearer / X-API-Key Header
activate Auth
Auth -> Auth: Constant-Time HMAC Comparison / JWT Decode
alt Authentication Failed
    Auth --> Client: HTTP 401 Unauthorized { "detail": "Invalid token or API key." }
end
deactivate Auth

Router -> Service: run_triage(request_dto, db_session)
activate Service

Service -> Repo: create_initial_request(text)
activate Repo
Repo -> DB: INSERT INTO triage_requests (raw_text, status='pending')
DB --> Repo: TriageRequest Object (ID=1)
Repo --> Service: req
deactivate Repo

Service -> Agent: classify_and_route(text) + draft_response(text)
activate Agent
Agent -> LLM: call_llm(prompt)
activate LLM

loop Retry Attempt 1..3 with Exponential Backoff (1s, 2s, 4s)
    LLM -> Gemini: generate_content(prompt)
    alt Gemini Success (200 OK)
        Gemini --> LLM: Raw JSON Text Response
    else Transient Rate Limit (429 / 503)
        Gemini --> LLM: HTTP 429 Resource Exhausted
        LLM -> LLM: Wait Backoff Duration & Retry
    end
end

alt LLM Exhaustion or Malformed JSON Validation Error
    LLM --> Agent: Raise LLMClientError / JSONParseError
    Agent --> Service: Exception Propagated
    Service -> DB: await session.rollback() (Discard Partial Writes)
    Service -> Repo: update_request_status(id=1, status='needs_review')
    Repo -> DB: UPDATE triage_requests SET status='needs_review'
    Service --> Router: Return TriageResponseDTO (status='needs_review')
    Router --> Client: HTTP 201 Created (Gracefully Degraded)
else Classification & Draft Success
    LLM --> Agent: Valid JSON Payload
    Agent --> Service: Dict { summary, category, priority, owner, draft }
    deactivate Agent
    deactivate LLM
    Service -> Repo: save_full_triage(id=1, classification, draft)
    Repo -> DB: INSERT INTO classifications & response_drafts, UPDATE status='classified'
    Service --> Router: TriageResponseDTO (status='classified')
    Router --> Client: HTTP 201 Created (Full Triage Package)
end

deactivate Service
deactivate Router
@enduml
```

---

## 🔍 Why Each Architectural Layer Is Present (Technical Justification)

### 1. **Decoupled Frontend (React 18 / Vite / GSAP)**
* **Why it exists**: Provides an immersive enterprise UI with real-time feedback (`ProgressiveLoader`), glassmorphism aesthetics, dynamic JWT decoding, and particle canvas rendering.
* **Technical Rationale**: Keeps client presentation logic isolated from API processing. Utilizes `apiFetch` with `AbortController` timeouts (15s/30s) to prevent frozen UI states.

### 2. **Authentication Middleware & HMAC Comparison**
* **Why it exists**: Secures protected endpoints using either JWT Bearer tokens or `X-API-Key` headers.
* **Technical Rationale**: Uses `hmac.compare_digest()` for constant-time string verification. This eliminates **timing side-channel attacks** where an attacker could deduce key characters by measuring CPU response micro-latencies.

### 3. **Pydantic DTO (Data Transfer Object) Boundary**
* **Why it exists**: Enforces strict payload contracts (`LoginRequestDTO`, `TriageRequestDTO`) at the perimeter of the application.
* **Technical Rationale**: Prevents malformed, truncated, or malicious payloads from reaching service domain logic, returning standard HTTP 422 validation errors automatically.

### 4. **Service Boundary & Transaction Rollback Order**
* **Why it exists**: Manages business workflows, orchestration, and database transactions (`src/services/triage_service.py`).
* **Technical Rationale**: Ensures **atomic state management**. In case of LLM failure or JSON parse error, calling `await session.rollback()` *before* updating `status = "needs_review"` guarantees that partially flushed ORM objects (e.g. invalid classification drafts) are discarded, preventing orphan records or database corruption.

### 5. **Two-Tier Error Handling Architecture**
* **Why it exists**: Separates expected domain failures from unexpected system crashes.
* **Technical Rationale**:
  * **Tier 1 (Domain LLM/Validation Errors)**: Catches `(JSONParseError, ValidationError, LLMClientError)`. Gracefully degrades request status to `"needs_review"` and returns HTTP 201 Created so business workflows are not blocked by LLM hiccups.
  * **Tier 2 (System/Database Crashes)**: Intercepts unhandled system exceptions in global exception handlers, logs full tracebacks to the database `ErrorLog` table, and returns clean HTTP 500 responses without exposing internal server internals.

### 6. **Asynchronous SQLite (`aiosqlite` + SQLAlchemy 2.0)**
* **Why it exists**: Handles database persistence asynchronously without blocking Python's event loop.
* **Technical Rationale**: Synchronous I/O operations block Uvicorn worker threads. `aiosqlite` allows FastAPI to serve high-concurrency requests while database reads and writes execute asynchronously.

### 7. **LLM Client Wrapper with Exponential Backoff**
* **Why it exists**: Manages raw interaction with the Google Gemini API (`src/agents/llm_client.py`).
* **Technical Rationale**: Implements automated retries for transient errors (HTTP 429 rate limits, 503 service unavailable) with exponential backoff (`1s`, `2s`, `4s`), ensuring resilience against upstream API instability.
