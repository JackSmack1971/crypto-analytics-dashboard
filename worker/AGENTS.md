# AGENTS.md: Worker Development Guide
<!-- Worker-specific AI collaboration guide for Python data processing workflows -->

## 1. Worker-Specific Overview
*   **Primary Goal:** Python worker processes handling data ingestion, normalization, valuation snapshots, Parquet generation, and data compaction with strict deterministic behavior.
*   **Core Functions:** CSV normalization with idempotency, time series valuation without forward-fill, portfolio calculations (FIFO/LIFO lots), Parquet snapshots (5m/1h/1d), and data compaction with RAM watermarks.
*   **Key Responsibilities:** Transaction processing, valuation pipeline, Parquet/DuckDB coordination, backup generation, FX drift monitoring, compaction with profiles.

## 2. Worker Technology Stack
*   **Runtime:** Python 3.12+
*   **Data Processing:** pandas for DataFrames, pyarrow for Parquet I/O
*   **Database:** SQLAlchemy async for SQLite operations, DuckDB for analytics queries
*   **File Format:** Parquet with partitioning (`dt=YYYY-MM-DD/asset_id=...`)
*   **Observability:** OpenTelemetry tracing, structured logging
*   **Package Manager:** pip/uv for dependency management

## 3. Worker Architecture Patterns
*   **Pipeline Processing:** ETL pipelines for ingestion → normalization → valuation → snapshots
*   **Event-Driven:** Process data based on triggers (new CSV, time boundaries, operator actions)
*   **Partition Management:** Time-based partitioning for efficient queries and compaction
*   **Memory Management:** RAM watermark monitoring (0.65 alert, 0.90 critical) with profiles
*   **State Persistence:** Track processing state, checkpoint progress, resume capability

## 4. Worker-Specific Coding Standards
*   **Module Organization:** Pipeline-based structure (`ingestion/`, `valuation/`, `snapshots/`, `compaction/`)
*   **Function Design:** Pure functions where possible, clear input/output contracts
*   **Error Handling:** Robust error handling with recovery, failed record quarantine
*   **Async Pattern:** Use asyncio for I/O operations, synchronous for computation
*   **Configuration:** Environment-based configuration with validation

## 5. Critical Data Processing Requirements

### CSV Ingestion & Normalization
*   **Schema Enforcement:** Strict Transactions CSV v1.1 validation
*   **ID Management:** UUIDv7 format validation and generation
*   **Idempotency:** Deduplicate via keys: `(account, tx_hash)` | `external_id` | `id`
*   **FEE Processing:** Always create negative quantity FEE rows
*   **Transfer Rules:** Preserve acquisition dates, produce no P&L impact
*   **Validation:** 10MB/100k row limits, formula character sanitization

### Valuation Pipeline Rules
*   **No Forward Fill:** Never interpolate missing price data
*   **Bucket Boundaries:** Precise 5m/1h/1d bucket-close logic including DST handling
*   **Provider Awareness:** Respect rate limits, handle 429/5xx gracefully  
*   **Provenance Tracking:** Persist `{price_source, resolution, asof}` with all data
*   **FX Handling:** Implement fallback FX with drift detection (`>25bps` threshold)
*   **Granularity Policy:** No forward fill across resolutions

### Portfolio Calculations
*   **Lots Engine:** Implement FIFO/LIFO lot tracking with acquisition date preservation
*   **Transfer Handling:** Move lots between accounts without P&L impact
*   **NAV Calculations:** Net Asset Value with proper FX conversion
*   **TWR/DD Metrics:** Time-Weighted Return and drawdown calculations
*   **Deterministic Behavior:** Reproducible results for same input data

### Parquet & Compaction Management  
*   **Partitioning:** Strict `dt=YYYY-MM-DD/asset_id=...` partition structure
*   **Row Groups:** DEFAULT profile ~128MB, LOW_RAM profile ~32MB
*   **RAM Watermark:** Monitor memory usage, alert at 65%, critical at 90%
*   **Compaction Profiles:** Configurable memory/performance trade-offs
*   **File Organization:** Optimize for both time-series and cross-sectional queries

## 6. Worker Development Workflow
*   **Local Development:**
    - Install dependencies: `cd worker && pip install uv && uv pip install -e .`
    - Run worker: `python -m worker.run`
*   **Testing:**
    - Unit tests: Focus on pure functions, data transformations
    - Integration tests: End-to-end pipeline testing with fixtures
    - Data quality tests: Validate output schemas and business rules
*   **Profiling:** Memory usage monitoring, performance benchmarking

## 7. Worker-Specific Instructions

### Data Ingestion Pipeline
*   **CSV Processing:** Stream large files, validate schema row-by-row
*   **Error Handling:** Quarantine invalid rows, continue processing valid data
*   **Progress Tracking:** Checkpoint progress for resume capability
*   **Validation Chain:** Schema → business rules → idempotency → normalization
*   **Output Generation:** Atomic writes, transaction rollback on failure

### Valuation Engine Implementation
*   **Time Alignment:** Precise bucket boundary calculations with timezone handling
*   **Provider Coordination:** Coordinate with API layer for rate-limited data fetching
*   **Price Discovery:** Handle missing data gracefully, no forward-fill
*   **FX Integration:** Multi-currency support with fallback mechanisms
*   **Snapshot Generation:** Materialize 5m/1h/1d views with full provenance

### Memory & Performance Management
*   **Streaming Processing:** Process large datasets without loading entirely into memory
*   **Batch Processing:** Optimal batch sizes for database operations
*   **Resource Monitoring:** Track memory usage, trigger compaction when needed
*   **Profile Selection:** Choose DEFAULT vs LOW_RAM based on available resources
*   **Garbage Collection:** Explicit memory cleanup for long-running processes

### File System Management
*   **Partition Creation:** Create date-based partitions automatically
*   **File Naming:** Consistent naming conventions for Parquet files
*   **Metadata Management:** Track file statistics, row counts, size metrics
*   **Cleanup Operations:** Remove old partitions based on retention policies
*   **Integrity Checks:** Verify file integrity after writes

### Backup & Recovery
*   **Backup Generation:** Nightly backup creation with manifest files
*   **Verification:** Integrity checks using SQLite PRAGMA and DuckDB scans
*   **Restore Drills:** Weekly automated restore testing
*   **Artifact Management:** Organize backup artifacts with checksums
*   **Recovery Procedures:** Point-in-time recovery capabilities

### DuckDB Integration
*   **View Definitions:** Create optimized views over Parquet partitions
*   **Query Optimization:** Leverage DuckDB's columnar processing
*   **Schema Evolution:** Handle schema changes gracefully
*   **Performance Tuning:** Optimize for typical analytics queries
*   **Connection Management:** Efficient connection pooling

### Monitoring & Observability
*   **Pipeline Metrics:** Track processing times, row counts, error rates
*   **Resource Metrics:** Memory usage, disk I/O, CPU utilization
*   **Data Quality Metrics:** Schema compliance, completeness, freshness
*   **Alert Thresholds:** Define alerting for pipeline failures, resource exhaustion
*   **Trace Correlation:** Link processing steps with trace_id

### Required Processing Modules
*   `ingestion.csv_processor` - CSV validation and normalization
*   `valuation.price_engine` - Time series valuation without forward-fill
*   `valuation.fx_handler` - Multi-currency conversion with drift detection
*   `portfolio.lots_engine` - FIFO/LIFO lot tracking
*   `portfolio.metrics` - NAV/TWR/drawdown calculations
*   `snapshots.parquet_writer` - Partitioned Parquet generation
*   `compaction.memory_manager` - RAM watermark monitoring
*   `compaction.file_compactor` - Parquet file optimization
*   `backup.generator` - Backup creation and verification
*   `backup.restore` - Recovery and drill procedures

### Forbidden Patterns
*   **DO NOT** forward-fill missing time series data
*   **DO NOT** load entire datasets into memory unnecessarily
*   **DO NOT** ignore RAM watermark alerts
*   **DO NOT** skip data validation steps
*   **DO NOT** create P&L impacts for transfer transactions
*   **DO NOT** process data without idempotency checks
*   **DO NOT** write to Parquet without proper partitioning

### Configuration Requirements
*   **Storage Profiles:** DEFAULT (performance) vs LOW_RAM (constrained)
*   **Memory Watermarks:** 65% warning, 90% critical thresholds
*   **Batch Sizes:** Configurable for different processing stages
*   **Retention Policies:** Data aging and cleanup schedules
*   **Provider Settings:** Rate limits, timeout configurations
*   **Backup Schedules:** Nightly backup at 02:30, weekly drills
