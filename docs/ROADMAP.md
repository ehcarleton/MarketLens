# MarketLens Roadmap (Aligned to Current Architecture)

This roadmap assumes a **part-time cadence (~2 hrs/day ≈ 10 hrs/week)**.
Each phase ends with a concrete deliverable and builds toward a **PyQt6, VS2022/Rider-style** desktop app, a **shared data-collection library**, **multi-provider** support, **multi-DB** backends, and **user-defined categorization**.

---

## Phase 1 — Foundations & Data Path (2–3 weeks)

**Goal:** Prove end-to-end ingestion → normalization → storage → query.

* [ ] Repo scaffold:
  `gui/`, `scheduler/`, `data_collection/`, `storage/`, `providers/`, `analysis/`, `categorization/`, `plugins/`, `cli.py`
* [ ] **Config**: `config.yaml` (DB backend, provider keys, resolver priority)
* [ ] **Storage**: `DatabaseConnector` (DuckDB default), schema initializer

  * Tables: `exchanges`, `symbols`, `profiles`, `fundamentals`, `prices`, `jobs`
* [ ] **Provider interface** + **FMP adapter** (profiles, balance sheet, ratios-TTM)
  + `capabilities()` + `list_markets()` probes
* [ ] **Normalization** layer: persist normalized columns **and** `raw_json`, with `source` + `ingested_at`
* [ ] CLI: `ml fetch --symbols AAPL,MSFT` to pull & store
* [ ] Basic derived view: `v_company_metrics (net_debt, simple joins)`

**Deliverable:** CLI-only prototype that ingests from FMP and writes to DuckDB with provenance.

---

## Phase 2 — Minimal Analysis & Breakout (2–3 weeks)

**Goal:** Compute first signals with fundamentals overlay.

* [ ] Breakout v1 (lookback high + volume multiple)
* [ ] Derived metrics: `net_debt`, `debt_to_equity` (computed locally)
* [ ] Views joining `prices + profiles + fundamentals`
* [ ] CLI: `ml screen` prints candidates (sector, industry, net_debt)
* [ ] Unit tests: breakout + fundamentals transforms

**Deliverable:** `ml screen` shows a sortable candidate table.

---

## Phase 3 — Headless Scheduling (2 weeks)

**Goal:** Automate what the GUI will also do manually.

* [ ] APScheduler wrapper (systemd/Task Scheduler friendly)
* [ ] Job lifecycle: `pending → running → success/fail` with retries/backoff
* [ ] `discover_markets` + `sync_symbols(exchange)` using provider capabilities
* [ ] `fetch_eod` daily @ close; job history persisted & viewable

**Deliverable:** Scheduler reliably pulls EOD; jobs visible in `jobs` table.

---

## Phase 4 — Desktop UI v1 (PyQt6, VS2022/Rider-style) (4–5 weeks)

**Goal:** Dynamic dockable UI; run analysis on demand.

* [ ] **PyQt6** app skeleton (`QMainWindow`, `QDockWidget`, `QSplitter`, `QSettings` for layout)
* [ ] **Main Work Area**: Candidates Grid (`QTableView` bound to `screen` results)
* [ ] **Explorer Panel** (dock): Watchlists, Sectors, Rule Sets, Recent
* [ ] **Properties Panel** (dock): profile/fundamentals + provenance drawer
* [ ] **Jobs/Logs Panel** (dock): show scheduler/one-off runs
* [ ] “**Refresh**” button runs screen; “**Fetch EOD now**” runs same library path
* [ ] Threading: `QThreadPool/QRunnable` for non-blocking fetch/screen

**Deliverable:** Open GUI → click *Refresh* → see candidates; *Fetch EOD now* works.

---

## Phase 5 — User-Defined Categorization Engine (3–4 weeks)

**Goal:** Make categories (like “weaker-dollar winners”) **rules, not columns**.

* [ ] Rule sets model: `rule_sets`, `rules(expression, color, order)`
* [ ] Tiny DSL / JSON-logic → SQL predicate compiler (targets **views**, not base tables)
* [ ] GUI **Rule Builder** (create, reorder, colorize, enable/disable)
* [ ] Grid **chips** rendering for active rule hits
* [ ] Import/Export rule sets (JSON)

**Deliverable:** Users define/share rule sets; chips appear in the grid.

---

## Phase 6 — Multi-Provider Fusion, Provenance & Overrides (3 weeks)

**Goal:** Multiple sources, conflict resolution, and manual control.

* [ ] Add 2nd provider skeleton (e.g., Polygon *or* EDGAR stub)
* [ ] Store per-field provenance; resolver priority in `config.yaml` (e.g., `edgar > polygon > fmp`)
* [ ] `geo_overrides` table + GUI override editor (e.g., foreign revenue %)
* [ ] **Provider Capabilities** panel: markets list, approx instrument counts, toggles

**Deliverable:** Same field from different providers reconciled deterministically; overrides honored and auditable.

---

## Phase 7 — Plugins & Extensibility (3–4 weeks)

**Goal:** Pluggable filters, charts, and rule libraries.

* [ ] `plugins/` discovery (entrypoint: `register(app)`)
* [ ] Plugin types:

  * Filters/indicators (extend screen)
  * Charts (extras in Chart View)
  * Rule libraries (prebuilt rule sets)
* [ ] Example plugins: **Relative Strength vs SPY**, **Debt/Equity filter**
* [ ] GUI auto-wires plugin actions and rule sets

**Deliverable:** Drop a `.py` into `plugins/` → new actions/rules appear.

---

## Phase 8 — Power-User & Production Features (ongoing)

**Goal:** Concurrency, performance, polish, packaging.

* [ ] **Postgres backend** (multi-process safe); optional **TimescaleDB** for OHLCV
* [ ] Materialized Views (Postgres) + refresh commands
* [ ] PyQtGraph charts (candles, volume; overlays for breakouts)
* [ ] Backfill jobs (1–5 years history, chunked/rate-limited)
* [ ] Export candidates/watchlists to CSV/Excel
* [ ] Packaging: PyInstaller builds for Win/macOS/Linux
* [ ] Quality: logging, telemetry **off** by default, richer tests

**Deliverable:** Daily-driver desktop app; GUI + Scheduler can run concurrently with Postgres.

---

## Timeline (at ~10 hrs/week)

* **Month 1:** Phases 1–2 → CLI prototype with signals & fundamentals
* **Month 2:** Phase 3 → Reliable scheduler
* **Months 3–4:** Phase 4 → First PyQt6 GUI (VS-style docking)
* **Month 5:** Phase 5 → Rule engine + chips + rule builder
* **Month 6:** Phase 6 → Multi-provider fusion, overrides
* **Month 7+:** Phases 7–8 → Plugins, Postgres, charts, backfills, packaging

---

## Invariants (apply across all phases)

* **GUI & Scheduler share the same `data_collection` library.**
* **Persist provider “facts” with `source` + `ingested_at`;** compute ratios/growth/categories locally in **views**.
* **Multi-DB:** DuckDB by default; Postgres for concurrency.
* **User-defined categorization** is first-class and exportable.
* **No cloud backend;** keys and data remain on the user’s machine.
