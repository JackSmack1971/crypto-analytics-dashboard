# AGENTS.md: Frontend Development Guide
<!-- Frontend-specific AI collaboration guide for the Next.js App Router UI -->

## 1. Frontend-Specific Overview
*   **Primary Goal:** Next.js App Router UI providing crypto portfolio analytics, asset charts with technical indicators, and operator console for system management during outages.
*   **User Experience:** Local-first design with offline capability, strict localhost binding (127.0.0.1), and operator controls for rate limiting, FX drift, and system health monitoring.
*   **Key Features:** CSV transaction import, real-time asset charts (candles + MA/RSI/MACD), portfolio NAV/TWR/drawdown, ETH gas & BTC mempool panels, comprehensive Operator Console.

## 2. Frontend Technology Stack
*   **Framework:** Next.js 14.2.5 with App Router (experimental appDir: true)
*   **Runtime:** Node.js 20+ with pnpm package manager
*   **Languages:** TypeScript 5.x, JavaScript ES2023
*   **Styling:** Tailwind CSS (inferred from project structure)
*   **Charts:** Chart.js/D3.js for data visualization (inferred from requirements)
*   **Testing:** Playwright for E2E tests, Jest for unit tests
*   **Service Worker:** Offline capability with stale-while-revalidate caching

## 3. Frontend Architecture Patterns
*   **App Router Structure:** Uses Next.js App Router with `/app` directory structure
*   **API Integration:** All external data fetched via FastAPI BFF at localhost endpoints only
*   **Component Architecture:** Feature-based organization (e.g., `features/portfolio`, `features/charts`, `features/operator-console`)
*   **State Management:** React Hooks for local state, Server Components where possible
*   **Capabilities Gating:** Components conditionally render based on `/capabilities` endpoint response

## 4. Frontend-Specific Coding Standards
*   **File Naming:** `kebab-case` for files, `PascalCase` for components, `camelCase` for variables/functions
*   **Component Structure:** Functional components with hooks, default exports for pages/components
*   **Data Fetching:** Use Next.js App Router patterns (Server Components, fetch with caching)
*   **Error Boundaries:** Implement for chart components and data-heavy sections
*   **Accessibility:** WCAG 2.2 compliance, proper focus management, ARIA labels for charts
*   **TypeScript:** Strict typing enabled, no `@ts-expect-error` or `@ts-ignore` allowed

## 5. Critical Frontend Requirements

### API Integration Rules
*   **Localhost Only:** All API calls must target `127.0.0.1:PORT` endpoints
*   **No Direct Provider Calls:** Never call CoinGecko, Etherscan, etc. directly from browser
*   **Rate Limit Handling:** Display appropriate UI states for 429 responses with `Retry-After`
*   **Capabilities Gating:** Check `/capabilities` endpoint to conditionally show ETH/BTC panels

### Data Display Rules  
*   **No Forward Fill:** Never interpolate missing time series data
*   **Provenance Display:** Show `{resolution, asof, source}` for all time series data
*   **Real-time Updates:** Use Server-Sent Events or polling for live data where applicable

### Operator Console Requirements
*   **Status Cards:** Display provider budgets, breaker states, cache hit rates, disk usage, FX drift queue, backup/drill status
*   **Controls:** Budget editor (50-100% clamps), breaker toggles with confirmation dialogs, compactor dry-run, "Use EOD Once" for FX
*   **Confirmation Dialogs:** All destructive actions require explicit confirmation with context
*   **Trace Correlation:** Display `trace_id` links for debugging operator actions

### Offline/Error States
*   **Offline Banner:** Show when service worker detects offline state with last `asof` timestamp  
*   **FX Drift Banner:** Display when `drift_bps > 25` with "Use EOD Once" action
*   **Disk Guard Banner:** Warning when free space < 2GB
*   **Loading States:** Skeleton UI for all async operations
*   **Error States:** Contextual error messages with retry actions and trace_id links

## 6. Frontend Development Workflow
*   **Dev Server:** `pnpm dev` runs Next.js dev server on `localhost:3000`
*   **Build:** `pnpm build` creates production build with `output: 'standalone'`
*   **Testing:** 
    - `pnpm test` for unit tests
    - `pnpm test:e2e` for Playwright E2E tests covering critical user journeys (UJ1-UJ4)
*   **Linting:** `pnpm lint --fix` for ESLint + Prettier formatting
*   **Type Checking:** Strict TypeScript with `tsc --noEmit`

## 7. Frontend-Specific Instructions

### Component Development
*   **Charts:** Implement using Chart.js with accessibility labels and textual summaries
*   **Forms:** All form inputs require proper validation and error states
*   **Dialogs:** Must trap focus and restore on close, use proper ARIA attributes
*   **Tables:** Include sorting, filtering for operator logs and data tables

### Performance Requirements  
*   **Core Web Vitals:** Optimize for LCP, INP, CLS per performance budgets
*   **Bundle Size:** Monitor and optimize bundle size, lazy load heavy components
*   **Caching:** Implement Service Worker for offline capability and stale-while-revalidate

### Security Guidelines
*   **CORS:** Strict CORS policy allowing only localhost origins
*   **CSP:** Content Security Policy headers for XSS protection  
*   **Input Sanitization:** Sanitize all user inputs, especially CSV upload content
*   **No Secrets:** Never include API keys or secrets in frontend code

### Testing Requirements
*   **Unit Tests:** Test all utility functions, form validation, state management
*   **Integration Tests:** Test API integration with mocked endpoints (Mock Service Worker)
*   **E2E Tests:** Playwright tests for critical user journeys (UJ1-UJ4)
*   **Visual Tests:** Screenshot comparison for charts and complex UI components
*   **Accessibility Tests:** Automated a11y testing with axe-core

### Forbidden Patterns
*   **DO NOT** make direct calls to external APIs (CoinGecko, Etherscan, etc.)
*   **DO NOT** bind to any interface other than 127.0.0.1
*   **DO NOT** forward-fill missing time series data
*   **DO NOT** use `@ts-expect-error` or `@ts-ignore`
*   **DO NOT** expose sensitive data in client-side code
*   **DO NOT** implement complex business logic in frontend (delegate to BFF)

### Required UI Components
*   `Banner.Offline` - Offline state indicator
*   `Banner.FXDriftHold` - FX drift warning with override action
*   `Banner.DiskGuard` - Low disk space warning
*   `Card.Status` - Operator console status cards (6 variants)
*   `Dialog.BreakerConfirm` - Breaker action confirmation
*   `Form.BudgetEditor` - Budget editing with validation
*   `Action.UseEODOnce` - Single-use FX override action
*   `Uploader.CSV` - Transaction CSV upload with validation
*   `Chart.Candles` - OHLCV charts with technical indicators
*   `Panel.Portfolio` - NAV/TWR/drawdown display
*   `Panel.OnChain.EthGas` / `Panel.OnChain.BtcMempool` - Capabilities-gated panels
*   `Logs.Table` - Operator console log viewer with trace correlation
