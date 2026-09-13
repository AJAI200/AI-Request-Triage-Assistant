# AI Request Triage Assistant — Evaluator & Technical Interview Q&A Guide

This guide contains **all potential technical questions** an evaluator, senior architect, or reviewer may ask regarding the design, security, performance, and implementation of the AI Request Triage Assistant application, complete with expert answers.

---

## 🎯 Category 1: Architecture & System Design

### Q1: Why did you choose FastAPI over Flask or Django for this application?
**Answer**:
* **Native Asynchronous I/O (`async`/`await`)**: FastAPI is built on Starlette and ASGI, enabling asynchronous request handling. This allows concurrent LLM API calls and database operations without blocking worker threads.
* **Automatic OpenAPI & Pydantic Validation**: FastAPI automatically generates interactive Swagger/ReDoc documentation and validates request/response payloads via Pydantic DTOs at compile time.
* **High Performance**: Outperforms Flask and Django in request throughput, operating near NodeJS and Go speeds.

---

### Q2: How does your system achieve "Graceful Degradation" when the LLM fails or returns invalid output?
**Answer**:
We implement a **Two-Tier Error Handling Boundary**:
1. **Tier 1 (Domain Failures)**: If the Gemini API returns a rate limit error (`429`), times out, or returns invalid JSON that fails validation, `triage_service.py` catches domain exceptions (`JSONParseError`, `ValidationError`, `LLMClientError`).
2. **Transaction Rollback & Status Update**: The service calls `await session.rollback()` to purge partial database writes, updates the request record status to `"needs_review"`, and returns a valid HTTP `201 Created` payload to the client. The request is queued for human review without breaking user workflows.
3. **Tier 2 (System Failures)**: Unhandled database crashes or critical errors are caught by global middleware, logged to the `ErrorLog` database table, and returned as clean HTTP 500 errors.

---

### Q3: Why is `await session.rollback()` necessary before updating a request status to `"needs_review"`?
**Answer**:
During execution, SQLAlchemy ORM may flush intermediate objects (e.g. partial `Classification` or `ResponseDraft` instances) into the transaction buffer. If an exception occurs during JSON parsing or validation, calling `session.commit()` without rolling back would persist corrupted or incomplete classification objects. Calling `await session.rollback()` first clears the transaction buffer, ensuring only the status update (`status = "needs_review"`) is cleanly committed.

---

## 🔒 Category 2: Security & Authentication

### Q4: Why did you use `hmac.compare_digest()` for `X-API-Key` validation instead of standard string equality (`==`)?
**Answer**:
Standard string equality (`key1 == key2`) terminates evaluation at the first non-matching character, introducing variable execution micro-latencies. Attackers can exploit this via **timing side-channel attacks** by submitting crafted keys and measuring response times to guess valid key characters one by one. `hmac.compare_digest()` guarantees **constant-time string comparison**, completely eliminating timing vulnerabilities.

---

### Q5: Why is storing JWT tokens in `localStorage` flagged as a security trade-off, and how would you fix it in production?
**Answer**:
* **Risk**: Tokens stored in `localStorage` are accessible by any JavaScript script executing within the document context. If an XSS vulnerability exists in the app or any third-party dependency, an attacker can steal the JWT.
* **Production Fix**: The backend should issue JWT tokens inside an `httpOnly`, `Secure`, `SameSite=Strict` HTTP cookie. JavaScript cannot access `httpOnly` cookies, preventing token exfiltration via XSS.

---

### Q6: How is CORS configured in FastAPI, and what edge case must be avoided with wildcard origins?
**Answer**:
According to the W3C CORS specification, browsers reject requests if `Access-Control-Allow-Origin: *` is combined with `Access-Control-Allow-Credentials: true`. In `src/main.py`, we explicitly set `allow_credentials=False` alongside `allow_origins=["*"]` to ensure strict browser specification compliance.

---

## 🤖 Category 3: AI & LLM Integration

### Q7: How does your LLM client handle API rate limits (`429 RESOURCE_EXHAUSTED`) or transient failures?
**Answer**:
`src/agents/llm_client.py` wraps the Gemini API call in an exponential backoff retry loop (attempting up to 3 retries with backoff delays of 1s, 2s, 4s). It inspects HTTP status codes (`429`, `503`) and SDK error attributes (`RESOURCE_EXHAUSTED`). If retries are exhausted, it raises a custom `LLMClientError` to trigger the Tier 1 fallback mechanism.

---

### Q8: How do you enforce structured JSON output from an LLM without relying on native function calling support in every model?
**Answer**:
1. **System Prompt Formatting**: The prompt explicitly enforces a JSON schema with exact keys (`summary`, `category`, `priority`, `priority_reason`, `owner`).
2. **Markdown Fenced Striping**: `src/utils/json_parser.py` strips Markdown code blocks (```json ... ```) and extracts raw JSON.
3. **Pydantic Validation**: `src/utils/validators.py` validates that extracted values belong to permitted lookup sets (`Billing`, `Finance`, `High`, etc.).

---

## ⚡ Category 4: Frontend & UI Performance

### Q9: How did you optimize the HTML5 Canvas animations to prevent battery drain and GPU lag?
**Answer**:
1. **Tab Visibility Pause**: Attached `document.addEventListener('visibilitychange')` to cancel `requestAnimationFrame` loops when `document.hidden` is `true`.
2. **Particle Throttling & Bounds**: Throttled particle generation on mousemove to a 40ms interval and hard-capped maximum particles to `150`.
3. **Accessibility**: Checked `window.matchMedia('(prefers-reduced-motion: reduce)')` to disable heavy animations for users with motion sensitivity.

---

### Q10: How does the frontend handle API server port variations or offline backends?
**Answer**:
Created a centralized API service (`src/services/api.js`) using `import.meta.env.VITE_API_BASE_URL` with an `AbortController` timeout (`15s` / `30s`). If a request hangs or fails, the controller aborts cleanly, and the UI transitions from `ProgressiveLoader` to a user-friendly error banner.

---

## 📊 Summary Matrix for Quick Reference

| Topic | Key Concept | Solution / Pattern Implemented |
| :--- | :--- | :--- |
| **Auth Timing Attacks** | Side-Channel Micro-latencies | `hmac.compare_digest()` constant-time check |
| **LLM Reliability** | Transient 429 / 503 Errors | Exponential backoff + `needs_review` fallback |
| **Transaction State** | Partial ORM object flushes | `await session.rollback()` before fallback commit |
| **CORS Spec** | Wildcard credentials error | `allow_origins=["*"]`, `allow_credentials=False` |
| **Canvas Performance** | Battery drain & 4K stutter | `visibilitychange` pause + particle array capping |
