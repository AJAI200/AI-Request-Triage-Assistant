# AI Request Triage Assistant — Production API Specification & Error Reference

**Version**: 1.0.0  
**Base URL**: `http://127.0.0.1:8000`  
**Content-Type**: `application/json`  
**Security Protocols**: JWT Bearer Token (`Authorization: Bearer <token>`) & API Key Header (`X-API-Key: <key>`)

---

## 📋 Table of Contents
1. [Overview & Architectural Standards](#overview--architectural-standards)
2. [Authentication & Security Protocols](#authentication--security-protocols)
3. [Global Response Headers](#global-response-headers)
4. [API Endpoints Reference](#api-endpoints-reference)
   - [1. User Authentication (`POST /auth/login`)](#1-user-authentication-post-authlogin)
   - [2. Submit Triage Request (`POST /triage`)](#2-submit-triage-request-post-triage)
   - [3. Get Triage Request by ID (`GET /triage/{request_id}`)](#3-get-triage-request-by-id-get-triagerequest_id)
   - [4. List Historical Triages (`GET /triage`)](#4-list-historical-triages-get-triage)
   - [5. System Dashboard UI (`GET /`)](#5-system-dashboard-ui-get-)
5. [Complete Exception & Error Scenario Matrix](#complete-exception--error-scenario-matrix)
6. [Global Error Envelope & DB Error Logging](#global-error-envelope--db-error-logging)

---

## 🏛️ Overview & Architectural Standards

The **AI Request Triage Assistant API** provides an automated solution for parsing, classifying, prioritizing, routing, and drafting responses for incoming business requests using Gemini LLM and FastAPI.

### Key Features:
- **Dependency Injection**: Routers utilize FastAPI `Depends()` for database session management (`get_async_db`) and repository access (`get_triage_repository`, `get_user_repository`).
- **Centralized Configuration**: All security keys, JWT parameters, algorithms, and timeouts are managed centrally via `src/settings.py`.
- **Latency Monitoring**: Execution time is calculated per request and returned in the HTTP header `X-Process-Time` and stored in the database.
- **Auditability & Observability**: Structured entry/exit logging across all layers and error logging into the database `ErrorLog` table.

---

## 🔒 Authentication & Security Protocols

All protected endpoints require either a **JWT Bearer Token** or an **API Key**.

### 1. JWT Bearer Authentication
Include the token in the standard HTTP `Authorization` header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
- **Algorithm**: `HS256`
- **Default Expiration**: `1440 minutes` (24 hours)

### 2. API Key Authentication
Include the API Key in the custom HTTP header:
```http
X-API-Key: node_solutions_secret_key_123
```

### Public / Unprotected Endpoints:
- `GET /` (Dashboard UI)
- `POST /auth/login` (Authentication)
- `GET /docs`, `GET /redoc`, `GET /openapi.json` (OpenAPI Swagger Documentation)
- `GET /static/*` (Static UI Assets)

---

## ⏱️ Global Response Headers

Every HTTP response returned by the API (success or error) contains performance metadata:

| Header Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `X-Process-Time` | String | Server processing latency in milliseconds | `142.58ms` |
| `Content-Type` | String | MIME type of response payload | `application/json` |

---

## 🚀 API Endpoints Reference

### 1. User Authentication (`POST /auth/login`)

Exchanges user credentials (`username` and `password`) for a signed JWT Access Token.

- **URL**: `/auth/login`
- **Method**: `POST`
- **Authentication**: None (Public)
- **Request Headers**: `Content-Type: application/json`

#### Request Body Schema (`LoginRequestDTO`):
```json
{
  "username": "admin",
  "password": "password123"
}
```

#### Success Response (`200 OK`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1Nzc4MTYwMH0.signature",
  "token_type": "bearer"
}
```

#### Exception / Error Responses:

##### A. 401 Unauthorized (Invalid Credentials)
```json
{
  "detail": "Invalid username or password"
}
```

##### B. 422 Unprocessable Entity (Validation Error)
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "password"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

### 2. Submit Triage Request (`POST /triage`)

Submits raw customer or internal text request for automated LLM classification, priority scoring, owner routing, and draft response generation.

- **URL**: `/triage`
- **Method**: `POST`
- **Authentication**: JWT Bearer Token OR API Key Header
- **Request Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <jwt_token>` OR `X-API-Key: <api_key>`

#### Request Body Schema (`TriageRequestDTO`):
```json
{
  "text": "Invoice NS-1048 appears to include the same implementation charge twice. Can someone review it before payment is processed Friday?"
}
```

#### Success Response — Fully Classified (`201 Created`):
```json
{
  "id": 1,
  "status": "classified",
  "raw_text": "Invoice NS-1048 appears to include the same implementation charge twice. Can someone review it before payment is processed Friday?",
  "summary": "Invoice NS-1048 contains a duplicate implementation charge requiring billing review before Friday payment processing.",
  "category": "Billing",
  "priority": "High",
  "priority_reason": "Duplicate charge query with an upcoming payment processing deadline on Friday.",
  "owner": "Finance",
  "draft_response": "Hi there, thank you for bringing this duplicate charge to our attention. Our Finance team is reviewing invoice NS-1048 and will resolve the duplicate charge prior to Friday's payment run.",
  "process_time_ms": 1245.82
}
```

#### Success Response — Graceful Fallback (`201 Created` with `status: "needs_review"`):
*Triggered automatically when the LLM returns an API error (e.g. 429 Rate Limit) or malformed output.*
```json
{
  "id": 2,
  "status": "needs_review",
  "raw_text": "The system experienced a temporary LLM API rate limit during automated parsing.",
  "summary": "Request received and queued for manual human triage.",
  "category": "Other",
  "priority": "Medium",
  "priority_reason": "Automated triage pipeline encountered a transient processing error.",
  "owner": "Client Success",
  "draft_response": "Hello, your request has been logged and queued for manual review by our team.",
  "process_time_ms": 842.15
}
```


#### Exception / Error Responses:

##### A. 400 Bad Request (Empty Text)
```json
{
  "detail": "Request text cannot be empty."
}
```

##### B. 401 Unauthorized (Missing or Invalid Authentication)
```json
{
  "detail": "Missing Authorization header or X-API-Key."
}
```
*or if token is expired:*
```json
{
  "detail": "Token has expired."
}
```
*or if token signature is invalid:*
```json
{
  "detail": "Invalid token or API key."
}
```

##### C. 422 Unprocessable Entity (Missing `text` property)
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "text"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

##### D. 500 Internal Server Error (LLM / Database Failure)
```json
{
  "detail": "An internal server error occurred. Please try again later."
}
```

---

### 3. Get Triage Request by ID (`GET /triage/{request_id}`)

Retrieves a single historical triaged request record by integer ID.

- **URL**: `/triage/{request_id}`
- **Method**: `GET`
- **Authentication**: JWT Bearer Token OR API Key Header
- **Path Parameters**:
  - `request_id` (integer, required): Database primary key ID (e.g. `1`).

#### Success Response (`200 OK`):
```json
{
  "id": 1,
  "status": "classified",
  "raw_text": "Invoice NS-1048 appears to include the same implementation charge twice...",
  "summary": "Invoice NS-1048 contains a duplicate implementation charge...",
  "category": "Billing",
  "priority": "High",
  "priority_reason": "Duplicate charge query with an upcoming payment processing deadline on Friday.",
  "owner": "Finance",
  "draft_response": "Hi there, thank you for bringing this duplicate charge...",
  "process_time_ms": 1245.82
}
```

#### Exception / Error Responses:

##### A. 404 Not Found (Invalid ID)
```json
{
  "detail": "Triage request #999 not found."
}
```

##### B. 401 Unauthorized
```json
{
  "detail": "Invalid token or API key."
}
```

##### C. 422 Unprocessable Entity (Non-integer ID)
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "request_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abc"
    }
  ]
}
```

---

### 4. List Historical Triages (`GET /triage`)

Retrieves a paginated list of historical triaged requests.

- **URL**: `/triage`
- **Method**: `GET`
- **Authentication**: JWT Bearer Token OR API Key Header
- **Query Parameters**:
  - `limit` (integer, optional): Maximum items to return (Default: `50`, Min: `1`, Max: `200`).

#### Success Response (`200 OK`):
```json
[
  {
    "id": 2,
    "status": "classified",
    "raw_text": "The client portal has been unavailable since this morning...",
    "summary": "Client portal downtime causing complete staff lockout.",
    "category": "System Outage",
    "priority": "Urgent",
    "priority_reason": "Critical operational outage locking staff out of customer records.",
    "owner": "IT Support",
    "draft_response": "Our IT Engineering team is actively investigating the client portal outage...",
    "process_time_ms": 980.14
  },
  {
    "id": 1,
    "status": "classified",
    "raw_text": "Invoice NS-1048 appears to include the same implementation charge twice...",
    "summary": "Invoice NS-1048 contains a duplicate implementation charge...",
    "category": "Billing",
    "priority": "High",
    "priority_reason": "Duplicate charge query with an upcoming payment processing deadline on Friday.",
    "owner": "Finance",
    "draft_response": "Hi there, thank you for bringing this duplicate charge...",
    "process_time_ms": 1245.82
  }
]
```

#### Exception / Error Responses:

##### A. 422 Unprocessable Entity (`limit` out of bounds)
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["query", "limit"],
      "msg": "Input should be less than or equal to 200",
      "input": 500
    }
  ]
}
```

##### B. 401 Unauthorized
```json
{
  "detail": "Missing Authorization header or X-API-Key."
}
```

---

### 5. System Dashboard UI (`GET /`)

Serves the web dashboard application interface.

- **URL**: `/`
- **Method**: `GET`
- **Authentication**: None (Public)
- **Response**: `200 OK` (`text/html`)

---

## ⚠️ Complete Exception & Error Scenario Matrix

| Status Code | Error Category | Trigger Scenario | Error Response Detail |
| :--- | :--- | :--- | :--- |
| **`400 Bad Request`** | Business Validation | Sending empty or whitespace-only text to `POST /triage` | `"Request text cannot be empty."` |
| **`401 Unauthorized`** | Auth Missing | No `Authorization` or `X-API-Key` header supplied | `"Missing Authorization header or X-API-Key."` |
| **`401 Unauthorized`** | Auth Expired | JWT token passed has passed expiration timestamp | `"Token has expired."` |
| **`401 Unauthorized`** | Auth Invalid | Invalid JWT signature or wrong API Key | `"Invalid token or API key."` |
| **`401 Unauthorized`** | Login Failure | Incorrect username or password on `POST /auth/login` | `"Invalid username or password"` |
| **`404 Not Found`** | Resource Missing | Request ID does not exist on `GET /triage/{id}` | `"Triage request #{id} not found."` |
| **`422 Unprocessable`** | Schema Violation | Missing required fields or wrong parameter data types | Standard FastAPI Pydantic validation array |
| **`500 Internal Error`**| System Failure | Database disconnect, unhandled exception, LLM API error | `"An internal server error occurred. Please try again later."` |

---

## 🛡️ Global Error Envelope & DB Error Logging

Whenever an unhandled server error occurs:
1. The global exception handler intercepts the exception.
2. The exact error message, module, function name, and full stack trace are written to the database `ErrorLog` table.
3. The response latency `process_time_ms` is attached to the error log entry.
4. The client receives a clean, standardized HTTP 500 JSON response:

```json
{
  "detail": "An internal server error occurred. Please try again later."
}
```
