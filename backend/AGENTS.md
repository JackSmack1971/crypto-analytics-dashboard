# AGENTS.md: Backend API Development Guide
<!-- Backend-specific AI collaboration guide for the FastAPI BFF -->

## 1. Backend-Specific Overview
*   **Primary Goal:** FastAPI Backend-for-Frontend (BFF) providing HTTP API layer between Next.js UI and data services, handling rate limiting, circuit breaking, and provider coordination.
*   **Architecture Role:** Orchestration layer that coordinates provider calls, implements rate limiting/breakers, manages CSV ingestion, and exposes Prometheus metrics.
*   **Key Responsibilities:** HTTP API endpoints, provider rate limiting with adaptive clamps, circuit breaker implementation, CSV transaction processing, capabilities gating, observability metrics.

## 2. Backend Technology Stack
*   **Framework:** FastAPI 0.115.0+ with Pydantic 2.8.0+ for data validation
*   **Runtime:** Python 3.12+, uvicorn ASGI server
*   **Data Layer:** SQLAlchemy ORM with SQLite, Redis for rate limiting/caching
*   **HTTP Client:** httpx or aiohttp for provider API calls (async)
*   **Observability:** OpenTelemetry (OTel) for tracing, Prometheus metrics export
*   **Package Manager:** pip/uv for dependency management

## 3. Backend Architecture Patterns
*   **API Layer:** RESTful endpoints following OpenAPI 3.0 specification
*   **Rate Limiting:** Token bucket pattern with Redis backend, fallback to in-process
*   **Circuit Breaker:** Half-open probing pattern for provider resilience
*   **Async Processing:** FastAPI async/await for I/O-bound operations
*   **Middleware Stack:** CORS, rate limiting, tracing, error handling middleware
*   **Provider Abstraction:** Unified interface for CoinGecko, Etherscan, mempool.space, FX sources

## 4. Backend-Specific Coding Standards
*   **File Organization:** Feature-based modules (`api/assets`, `api/portfolio`, `api/onchain`)
*   **Function Naming:** `snake_case` for all functions, variables, modules
*   **Class Naming:** `PascalCase` for classes, Pydantic models
*   **Async Pattern:** Use `async def` for all I/O operations, `await` for external calls
*   **Error Handling:** Custom exception hierarchy with structured error codes
*   **Type Hints:** Full type annotations required, use Pydantic for data validation

## 5. Critical API Requirements

### HTTP Endpoint Implementation
*   **Required Endpoints:**
    - `GET /health` - Service health check with uptime/version info
    - `GET /capabilities` - Feature gating based on environment keys  
    - `GET /assets/{asset_id}/candles` - OHLCV data with technical indicators
    - `POST /portfolio/holdings/import` - CSV transaction import
    - `GET /onchain/eth/gas` - Ethereum gas prices (capabilities-gated)
    - `GET /onchain/btc/mempool` - Bitcoin mempool data (capabilities-gated)
    - `GET /assets/{asset_id}/metrics` - Asset-specific analytics
    - `GET /metrics` - Prometheus metrics export

### Response Standards
*   **Success Responses:** Include `{resolution, asof, source}` for all time series data
*   **Error Responses:** Structured errors with canonical codes and trace_id
*   **Rate Limit Responses:** 429 with `Retry-After` header when rate limited
*   **Capabilities Responses:** `{enabled: boolean}` for gated features
*   **Never Forward-Fill:** Preserve data granularity, no interpolation

### Rate Limiting Implementation
*   **Provider Budgets:** CoinGecko `{per_min:30, per_sec:5}`, Etherscan `{per_sec:5, per_day:100000}`, mempool.space `{per_sec:1}`, FX `{per_min:10}`
*   **Adaptive Clamps:** 50-100% range in 10% steps, 60s cooldown, 2x hysteresis
*   **Circuit Breaker:** Open on 429/5xx, half-open probes, manual operator override
*   **Freeze on 403:** Complete halt of provider calls until manual recovery
*   **Redis Fallback:** In-process leaky bucket with default-deny on Redis outage

### Data Processing Rules
*   **CSV Ingestion:** Enforce Transactions CSV v1.1 schema, UUIDv7 IDs, idempotency keys
*   **FEE Normalization:** Always create negative quantity FEE rows
*   **Transfer Handling:** Preserve acquisition dates, no P&L impact
*   **Validation:** Schema validation, 10MB/100k row limits, formula sanitization

## 6. Backend Development Workflow
*   **Local Development:** 
    - Install dependencies: `cd backend && pip install uv && uv pip install -e .`
    - Run server: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
*   **Testing:**
    - Unit tests: `pytest backend/tests/` 
    - Coverage: `pytest --cov` (target >90% for new code)
    - Mock external dependencies with fixtures
*   **Contract Validation:** OpenAPI spec compliance, JSON Schema validation
*   **Linting:** `black . && isort . && flake8 .`

## 7. Backend-Specific Instructions

### Provider Integration
*   **API Clients:** Implement async HTTP clients for each provider
*   **Error Handling:** Distinguish between 4xx client errors, 5xx server errors, timeouts
*   **Retry Logic:** Exponential backoff with jitter, respect `Retry-After` headers
*   **Caching:** Redis caching with TTL, cache warming for frequently accessed data
*   **Monitoring:** Export provider-specific metrics (request count, latency, error rate)

### Rate Limiting & Circuit Breaking
*   **Token Buckets:** Implement per-provider, per-route buckets in Redis
*   **Clamp Logic:** Adjust rates based on error rates, implement cooldown periods
*   **Breaker States:** CLOSED (normal) → OPEN (failing) → HALF_OPEN (probing) → CLOSED
*   **Operator Controls:** API endpoints for manual breaker control, budget adjustment
*   **Metrics Export:** Counters for 429s, breaker state changes, clamp adjustments

### Data Validation & Security
*   **Pydantic Models:** Define schemas for all request/response data
*   **CSV Validation:** Strict schema enforcement, size limits, formula sanitization
*   **CORS Policy:** Restrict to localhost origins only
*   **Input Sanitization:** Validate all user inputs, prevent injection attacks
*   **Secret Handling:** Load from environment variables, never log secrets

### Observability Implementation
*   **Tracing:** OpenTelemetry spans for all external calls and processing steps
*   **Metrics:** RED metrics (Rate, Errors, Duration) plus business metrics
*   **Logging:** Structured JSON logs with trace_id correlation
*   **Health Checks:** Comprehensive health endpoint checking dependencies
*   **Performance:** Monitor p95/p99 latencies per SLO targets

### Database Integration
*   **SQLAlchemy:** Use async SQLAlchemy for database operations
*   **Migrations:** Alembic for schema migrations (if needed)
*   **Connection Pooling:** Optimize connection pool settings for local SQLite
*   **Query Optimization:** Efficient queries for portfolio calculations

### Required Integrations
*   **Worker Communication:** Message queue or direct DB coordination with worker processes
*   **Redis Integration:** Rate limiting buckets, caching, session storage
*   **File Handling:** CSV upload processing, Parquet file coordination
*   **Backup Coordination:** Trigger backup processes, verify backup integrity

### Forbidden Patterns
*   **DO NOT** bind to any interface other than 127.0.0.1
*   **DO NOT** forward-fill missing time series data
*   **DO NOT** log sensitive data (API keys, transaction details)
*   **DO NOT** make provider calls without rate limiting
*   **DO NOT** ignore circuit breaker states
*   **DO NOT** expose internal errors to clients without sanitization

### Error Code Standards
*   `client_invalid_contract` - Schema/validation violations (4xx)
*   `provider_throttled` - Rate limiting active (429 + Retry-After)
*   `provider_banned` - 403 responses trigger freeze
*   `provider_outage` - 5xx errors open circuit breakers
*   `fx_drift_hold` - FX fallback drift >25bps holds NAV
*   `disk_guard_low_space` - Storage threshold alerts
