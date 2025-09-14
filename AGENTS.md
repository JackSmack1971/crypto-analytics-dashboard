# AGENTS.md: AI Collaboration Guide
<!-- This document provides essential context for AI models interacting with this project. Adhering to these guidelines will ensure consistency, maintain code quality, and optimize agent performance. -->

<!-- It is Saturday, September 13, 2025. This guide is optimized for clarity, efficiency, and maximum utility for modern AI coding agents like OpenAI's Codex, GitHub Copilot Workspace, and Claude. -->

<!-- This file should be placed at the root of your repository. More deeply-nested AGENTS.md files (e.g., in subdirectories) will take precedence for specific sub-areas of the codebase. Direct user prompts will always override instructions in this file. -->

## 1. Project Overview & Purpose
*   **Primary Goal:** Local-first, single-user crypto analytics dashboard providing fast charts (candles + MA/RSI/MACD), portfolio NAV/TWR/drawdown analysis, and operational controls during provider outages/limits. Data flows from Transactions CSV v1.1 through deterministic valuation pipeline to Parquet analytics read via DuckDB views.
*   **Business Domain:** Financial Technology (FinTech) - Cryptocurrency Portfolio Management and Analytics.
*   **Key Features:** CSV transaction import with idempotency, real-time asset price charts with technical indicators, portfolio performance metrics (NAV/TWR/DD), ETH gas & BTC mempool monitoring, Operator Console for system management during outages.

## 2. Core Technologies & Stack
*   **Languages:** Python 3.12+ (FastAPI, worker processes), TypeScript 5.x (Next.js frontend), JavaScript ES2023.
*   **Frameworks & Runtimes:** Next.js App Router (frontend), FastAPI (BFF API), Python asyncio (worker), Docker Compose (orchestration).
*   **Databases:** SQLite (primary transactional data), Redis (rate limiting & caching), Parquet (analytics storage), DuckDB (query views over Parquet).
*   **Key Libraries/Dependencies:** 
    - Frontend: React 18, Tailwind CSS, Chart.js/D3.js for visualization, Service Worker for offline capability
    - Backend: FastAPI, SQLAlchemy, pandas, pyarrow (Parquet), duckdb-python
    - Observability: OpenTelemetry (OTel), Prometheus metrics
*   **Package Manager:** pnpm (JavaScript/TypeScript), pip/uv (Python), Docker Compose for orchestration.
*   **Platforms:** Local development (127.0.0.1 binding only), Docker containers, Linux/macOS/Windows via Docker.

## 3. Architectural Patterns & Structure
*   **Overall Architecture:** Three-tier local-first architecture with strict localhost binding. Next.js UI calls FastAPI BFF which coordinates with Python worker processes. All external provider calls are rate-limited and circuit-broken. Data flows: CSV import → SQLite → Worker snapshots → Parquet → DuckDB views → UI charts.
*   **Directory Structure Philosophy:**
    *   `/frontend`: Next.js App Router UI with components, pages, and Operator Console
    *   `/backend`: FastAPI BFF handling HTTP API, rate limiting, and provider coordination  
    *   `/worker`: Python processes for data ingestion, normalization, valuation, and Parquet generation
    *   `/docs`: Comprehensive project documentation including contracts, security, and operational guides
    *   `/registry`: Asset registry (JSON-first, authoritative) for seeding database
    *   `/data`: Runtime data directory for SQLite, Parquet files, and backups
*   **Module Organization:** 
    - Frontend uses feature-based structure (e.g., `features/portfolio`, `features/charts`, `features/operator-console`)
    - Backend organized by domain (e.g., `api/assets`, `api/portfolio`, `api/onchain`)
    - Worker uses pipeline-based modules (e.g., `ingestion`, `valuation`, `snapshots`, `compaction`)

## 4. Coding Conventions & Style Guide
*   **Formatting:** 
    - Python: Black formatter, isort for imports, line length 100 characters
    - TypeScript/JavaScript: Prettier with 2-space indentation, single quotes, trailing commas
    - All code MUST pass lint checks before committing
*   **Naming Conventions:**
    - Python: `snake_case` for variables/functions/files, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants
    - TypeScript: `camelCase` for variables/functions, `PascalCase` for components/types/interfaces, `kebab-case` for files
    - Database: `snake_case` for tables/columns, UUIDv7 format for all IDs
*   **API Design Principles:** 
    - RESTful HTTP endpoints with comprehensive OpenAPI documentation
    - Always document 2xx/4xx/5xx responses including 429 with `Retry-After` headers
    - Rate-limited endpoints must implement adaptive clamps (50-100% in 10% steps)
    - All responses include provenance data: `{resolution, asof, source}` for time series
*   **Documentation Style:** 
    - Python: Comprehensive docstrings for all public functions and classes
    - TypeScript: JSDoc comments for components and complex functions
    - All public API changes require OpenAPI specification updates
*   **Error Handling:**
    - Python: Custom exception hierarchy with structured error codes
    - Rate limiting: Honor `Retry-After` headers, implement circuit breakers with half-open probes
    - Provider 403 responses trigger immediate freeze until manual recovery
    - All errors must include `trace_id` for correlation

## 5. Development & Testing Workflow
*   **Local Development Setup:**
    1. **Prerequisites:** Docker & Docker Compose, Node.js 20+, Python 3.12+
    2. **Environment Setup:** Copy `.env.example` to `.env`, configure provider API keys for full functionality
    3. **Container Orchestration:**
       ```bash
       # Start core services (UI, API, Redis)
       docker compose up
       
       # Add worker processes
       docker compose --profile worker up -d
       
       # Add observability stack
       docker compose --profile ops up -d
       ```
    4. **Health Verification:** `GET http://127.0.0.1:PORT/health` should return healthy status
*   **Build Commands:**
    - Frontend: `cd frontend && pnpm build`
    - Backend: `cd backend && pip install -e .`
    - Full stack: `docker compose build`
*   **Testing Commands:** **All new code MUST have corresponding unit tests.**
    - Python tests: `pytest backend/tests/` (must mock external dependencies)
    - Frontend tests: `cd frontend && pnpm test` (use Mock Service Worker for API mocking)
    - Contract tests: Validate OpenAPI spec compliance and JSON Schema adherence
    - E2E tests: `pnpm test:e2e` (Playwright for critical user journeys UJ1-UJ4)
    - **MUST** run `pytest --cov` for Python coverage and ensure >90% coverage for new code
*   **Linting/Formatting Commands:** **All code MUST pass lint checks before committing.**
    - Python: `black . && isort . && flake8 .` 
    - Frontend: `pnpm lint:fix && pnpm format`
    - All: `make check` (runs all linting and formatting checks)
*   **CI/CD Process Overview:** GitHub Actions runs on every PR: linting, type checking, unit tests, contract validation, security scans (Gitleaks), dependency audits (pip-audit, npm audit), and E2E tests. All checks must be green before merge.

## 6. Git Workflow & PR Instructions
*   **Pre-Commit Checks:** **ALWAYS** run `make check` (linting, formatting, type checking) and `make test` before committing. Use pre-commit hooks to enforce this.
*   **Branching Strategy:** Work on feature branches, create PRs against `main`. **DO NOT** commit directly to `main` or work on the `main` branch.
*   **Commit Messages:** Follow Conventional Commits specification:
    - `feat(scope): description` for new features
    - `fix(scope): description` for bug fixes  
    - `docs(scope): description` for documentation
    - Include "BREAKING CHANGE:" in body for breaking changes
*   **Pull Request Process:**
    1. Ensure branch is up-to-date with `main` and conflicts are resolved
    2. Run full test suite and verify all checks pass locally
    3. Update relevant documentation (OpenAPI, data contracts, etc.)
    4. Create PR with clear title and description linking to issues
    5. Code owner review required for critical paths (API, Operator Console)
*   **Force Pushes:** **NEVER** use `git push --force` on `main` branch. Use `git push --force-with-lease` on feature branches only if necessary.
*   **Clean State:** **You MUST leave your worktree in a clean state after completing a task** (no uncommitted changes, no untracked files).

## 7. Security Considerations
*   **General Security Practices:** **Be extremely security-aware** - this handles financial data. Follow principle of least privilege and validate all inputs.
*   **Sensitive Data Handling:** 
    - **DO NOT** hardcode any secrets, API keys, or credentials in code
    - Load all sensitive data from environment variables (classified as Secret)
    - CSV inputs and Parquet analytics are classified as Confidential
*   **Input Validation:** 
    - **ALWAYS** validate and sanitize all user inputs on both frontend and backend
    - CSV uploads: enforce strict schema, 10MB/100k row limits, escape formula-leading characters
    - API inputs: comprehensive validation with structured error responses
*   **Network Security:**
    - **ALL services MUST bind to 127.0.0.1 only** - never expose to external networks
    - Implement strict CORS policy allowing only localhost origins
    - No external dependencies should be directly accessible from frontend
*   **Vulnerability Avoidance:** 
    - Prevent common CWEs: injection attacks, path traversal, insecure deserialization
    - Regular dependency updates and security scanning via pip-audit/npm audit
    - Gitleaks CI gate prevents secret leakage

## 8. Specific Agent Instructions & Known Issues
*   **Tool Usage:**
    - Use `uv` for Python dependency management instead of `pip` or `virtualenv`
    - Use `pnpm` for Node.js packages, never `npm` or `yarn`
    - Use Docker Compose for local development environment
*   **Context Management:** 
    - For large changes affecting >5 files, break into smaller, focused PRs
    - Create implementation plan first, then execute incrementally
    - Each PR should be self-contained and testable
*   **Quality Assurance & Verification:** 
    - **ALWAYS** run the full test suite after making changes
    - Verify backup/restore functionality works: `make backup.verify`
    - Check `/metrics` endpoint returns valid Prometheus format
    - Validate rate limiting works under synthetic 429/5xx conditions
    - **DO NOT** report completion until ALL programmatic checks pass
*   **Project-Specific Quirks:**
    - **NEVER forward-fill time series data** - always preserve data granularity with `{resolution, asof, source}`
    - Transfers between accounts must preserve acquisition dates and produce **no P&L**
    - FEE transactions must always include negative quantity FEE rows
    - Rate limiting clamps are bounded: min 50%, max 100%, step 10%
    - All UUIDs must be UUIDv7 format for time-sortable properties
*   **Forbidden Patterns:**
    - **NEVER** use `@ts-expect-error` or `@ts-ignore` to suppress TypeScript errors
    - **DO NOT** bind services to 0.0.0.0 or external interfaces
    - **NEVER** log or expose sensitive data (API keys, transaction details)
    - **DO NOT** implement forward-fill for missing price data
    - **NEVER** allow CSV formula execution or unsafe deserialization
*   **Troubleshooting & Debugging:** 
    - If tests fail, provide the **full stack trace** for proper debugging
    - Use structured logging with `trace_id` correlation for distributed tracing
    - Check Operator Console status cards for system health issues
    - Validate backup integrity with `make backup.verify` if data corruption suspected