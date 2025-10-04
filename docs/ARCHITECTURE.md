# MarketLens Architecture

> **An open, private, extensible platform for serious stock analysis — built together.**
> Version: Draft 3 — PyQt6, dynamic VS2022/Rider-style UI, user-defined categorization, shared data-collection library, multi-provider & multi-DB.

---

## 1) Purpose & Scope

MarketLens is a **local-first desktop tool** for end-of-day (EOD) analysis.
It is **not a trading bot**. Core goals:

* Pull EOD prices and company fundamentals from **user-selected providers**.
* Detect breakouts and other signals **locally**.
* Let users create **their own categorizations** (e.g., “weaker-dollar winners”), shareable as rules/plugins.
* Keep data and keys **on the user’s machine**.

---

## 2) Architectural Principles

1. **Local & Private** – No cloud backend; keys stored locally.
2. **Bring Your Own Data** – Pluggable providers; user chooses which to enable.
3. **One Engine, Two Apps** – A **shared data-collection library** is used by:

   * **Desktop GUI** (PyQt6): manual runs, analysis, visualization.
   * **Scheduler**: automates **exactly** what the GUI can do.
4. **Multi-DB** – DuckDB (default) and Postgres (concurrent/power users).
5. **Persist vs Compute** – Provider “facts” are **persisted with provenance**; metrics & labels are **computed locally** (views/pipelines).
6. **User-Defined Categorization** – Categories are **rules**, not hard-coded fields.
7. **Extensible** – Providers, storage backends, analysis/categorization rules, and UI panels are plugin-friendly.

---

## 3) High-Level Diagram

```text
            ┌─────────────────────────────────────────────────┐
            │               Providers (BYO keys)              │
            │   FMP, Polygon, Finnhub, SEC EDGAR, …           │
            └───────────────┬─────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────────────┐
                │  Data Collection Library      │  ← shared by GUI & Scheduler
                │  (sources, jobs, normalizers) │
                └───────────┬───────────┬───────┘
                            │           │
                            │           │
         Manual / On-Demand │           │ Scheduled / Automated
                            │           │
                            ▼           ▼
               ┌────────────────┐   ┌─────────────────┐
               │   Desktop GUI   │   │   Scheduler     │
               │   (PyQt6)       │   │ (APScheduler)   │
               └──────┬──────────┘   └──────┬──────────┘
                      │                     │
                      └──────────┬──────────┘
                                 ▼
                      ┌──────────────────────────┐
                      │      Storage Layer       │
                      │  DuckDB  |  Postgres     │
                      └───┬────────────┬─────────┘
                          │            │
                          ▼            ▼
          ┌────────────────────────────┐  ┌──────────────────────────────┐
          │  Analysis Pipelines        │  │  Categorization Engine       │
          │  (views, metrics, signals) │  │  (rule sets & plugins)       │
          └────────────────────────────┘  └──────────────────────────────┘
```

---

## 4) Desktop GUI (PyQt6) — Dynamic VS2022/Rider-Style

**Tech:** PyQt6 (GPL/commercial)
**Package:** `marketlens/gui`

### 4.1 Layout & Docking

* **Main Work Area** (central): charts, tables, backtests.
* **Side Panel — Explorer** (dockable/float/auto-hide):

  * **Lists of symbols** grouped by *Watchlists*, *Sectors*, *Rule Sets*, *Recent*.
  * Uses `QTreeView`/`QListView` + `QAbstractItemModel`.
* **Properties Panel** (dockable): read-only **Profile & Fundamentals** for the selected symbol; audit/provenance drawer.
* **Jobs/Logs Panel** (dockable): running/completed jobs, provider rate-limit info.
* **Status Bar**: DB mode (DuckDB/Postgres), provider status, last sync time.

**Qt constructs:** `QMainWindow` + `QDockWidget` + `QSplitter` for resizable panes; **layout is persisted** via `QSettings` and restorable per workspace.

### 4.2 Interactivity & State

* **Selection Model:** single source of truth (`QItemSelectionModel`) publishes the “current symbol”; all panels react via signals/slots.
* **Event Bus:** thin pub/sub for cross-panel events (e.g., `symbolSelected`, `jobCompleted`, `ruleSetChanged`).
* **Asynchronous tasks:** long-running calls (fetch, backfill, heavy queries) run in `QThreadPool` (`QRunnable`) to keep UI responsive.

### 4.3 Screens & Widgets

* **Candidates Grid** (central tab): filterable/sortable `QTableView`, chips for categories.
* **Chart View**: OHLCV + breakout overlays (PyQtGraph/Matplotlib).
* **Rule Builder**: create/edit rule sets (see §8).
* **Provider Capabilities**: discover markets, symbol counts, toggle providers.
* **Manual “Run Now”**: invoke any job the scheduler can run (same code paths).

---

## 5) Scheduler

**Tech:** Python, APScheduler (systemd/Task Scheduler friendly)
**Package:** `marketlens/scheduler`

* Runs **the same library APIs** as the GUI (`data_collection`).
* Typical jobs: `discover_markets`, `sync_symbols`, `fetch_eod`, `fetch_profiles`, `fetch_fundamentals`, `recompute_views`.
* Job table tracks `pending/running/succeeded/failed` with retries/backoff.

---

## 6) Shared Data-Collection Library

**Package:** `marketlens/data_collection`

Responsibilities:

* **Provider adapters** (normalize + store raw JSON).
* **Job orchestration** (idempotent, retryable).
* **Writes** to storage via a backend-agnostic repository layer.

### 6.1 Provider Interface & Capabilities

```python
class ProviderCapabilities(TypedDict):
    id: str               # 'fmp', 'polygon', 'edgar'
    name: str
    markets: list[dict]   # [{exchange_id, name, mic, tz, currency, approx_instruments}]
    supports: dict        # {'prices': True, 'profiles': True, 'fundamentals': True}
    rate_limit: str | None

class Provider(Protocol):
    def capabilities(self) -> ProviderCapabilities: ...
    def list_markets(self) -> list[dict]: ...
    def list_symbols(self, exchange_id: str) -> list[dict]: ...
    def fetch_eod(self, symbols: list[str], start=None, end=None) -> pd.DataFrame: ...
    def fetch_profiles(self, symbols: list[str]) -> pd.DataFrame: ...
    def fetch_fundamentals(self, symbols: list[str], period: str) -> pd.DataFrame: ...
```

* GUI uses `capabilities()` to **populate Markets** and expected symbol counts in real time.
* **Normalization rule:** map provider fields → standard columns **and** store `raw_json` + `source` + `ingested_at`.

---

## 7) Storage Layer

**Tech:** DuckDB (default) or Postgres (optional TimescaleDB)
**Package:** `marketlens/storage`

* `DatabaseConnector` chooses backend (env/config).
* Schema is **identical** across backends; Postgres may add indexes/MVs.

### 7.1 Persisted “Facts” (with provenance)

* `exchanges(exchange_id, name, country, mic, timezone, currency, provider_code, instruments_count, instruments_count_asof)`
* `symbols(symbol, company_id, exchange_id, is_active, instrument_type, first_seen, last_seen)`
* `profiles(company_id, name, sector, industry, country, market_cap, commodity_exposure,
           segments_json, geo_rev_foreign_pct, geo_rev_domestic_pct,
           source, ingested_at, raw_json)`
* `fundamentals(company_id, fiscal_date, period, cash, total_debt, revenue,
                eps_basic, eps_diluted, gross_margin, operating_margin,
                source, ingested_at, raw_json)`
* `prices(symbol, date, open, high, low, close, volume, source, ingested_at, raw_json)`
* `jobs(id, kind, payload_json, status, run_after, attempts, last_error, updated_at)`

### 7.2 Derived (always computed locally)

Views / MVs (DuckDB views; Postgres MVs):

* `v_company_metrics` → `net_debt`, YoY/TTM growth, leverage/quality flags, resolved geo percentages.
* `v_symbol_latest_price`, `v_symbol_returns`, indicator helpers for screening.

### 7.3 Multi-Source Resolution & Overrides

* Resolver priority (configurable): e.g., `edgar > polygon > fmp`.
* **Manual overrides**: `geo_overrides(company_id, foreign_pct_override, note, updated_at)`.
* Views use `COALESCE(override, provider_value, NULL)`; never mix guesses with persisted facts.

---

## 8) Categorization Engine (User-Defined Rules)

Categories are **rules** users (or plugins) define; results render as **chips** in the grid and drive watchlist/grouping.

### 8.1 Rule Model

* `rule_sets(id, name, description, version, created_at, updated_at)`
* `rules(id, rule_set_id, name, expression, color, order_index)`

The **expression** is a tiny DSL or JSON-logic compiled to SQL predicates against **views**.

**Examples**

```
is_export_heavy:           geo_rev_foreign_pct >= 0.50
is_domestic_manufacturer:  sector == "Industrials" and geo_rev_domestic_pct >= 0.70
is_commodity_producer:     commodity_exposure != "none"
is_international_revenue:  sector in ["Technology","Communication Services"] and geo_rev_foreign_pct >= 0.30
```

### 8.2 Evaluation & UI

* Engine compiles to SQL; returns boolean columns per rule.
* Grid shows colored chips; **multiple rule sets can be active**.
* Rule Builder panel supports **save/export/import** (JSON).
* Plugins can add **functions** usable in rules (e.g., `rs("SPY", "90d")`).

---

## 9) Concurrency & Modes

* **DuckDB mode** → single process; use either GUI **or** Scheduler at a time (GUI provides **Run Now** for manual users).
* **Postgres mode** → concurrent safe (GUI + Scheduler + external tools).
* Postgres uses **materialized views** (refresh on demand); DuckDB uses plain views.

---

## 10) Configuration

`config.yaml`

```yaml
database:
  type: duckdb           # or postgres
  path: ./data/marketlens.duckdb
  # postgres: host, db, user, password

providers:
  enabled: [fmp]
  fmp:
    api_key: "<YOUR_KEY>"

scheduler:
  timezone: America/New_York
  jobs:
    discover_markets:   "weekly:Mon 05:00"
    sync_symbols:       "weekly:Mon 05:15"
    fetch_eod:          "daily:16:05"
    fetch_fundamentals: "daily:02:00"

categorization:
  resolver_priority: [edgar, polygon, fmp]
ui:
  layout_profile: "vs2022"      # persisted dock layout
```

---

## 11) Code Layout

```
MarketLens/
├── src/
│   └── marketlens/
│       ├── gui/ …                        # PyQt6 app
│       ├── scheduler/ …                  # APScheduler service
│       ├── data_collection/ …            # providers, jobs, normalize
│       ├── storage/ …                    # connector, schema, repos
│       ├── analysis/ …                   # signals, views.sql, views_pg.sql
│       ├── categorization/ …             # rule engine + builtin_rules
│       ├── plugins/ …                    # samples + plugin API
│       ├── cli.py                        # Typer CLI (recommended)
│       ├── __init__.py                   # exports __version__ via setuptools-scm
│       └── py.typed                      # mark package as typed (PEP 561)
│
├── tests/                                # pytest (unit/integration)
│   ├── integration/                      # DB/Provider tests, can use Testcontainers
│   ├── conftest.py
│   └── test_*.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
│
├── packaging/
│   └── pyinstaller/
│       └── marketlens.spec               # GUI packaging recipe (later)
├── .github/workflows/
│   └── ci.yml                            # lint + type + test on push/PR
├── .pre-commit-config.yaml
├── .editorconfig
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt                      # optional; prefer pyproject + lock
├── pyproject.toml                        # single source of truth (build + tools)
└── uv.lock / requirements-lock.txt       # pick ONE lock strategy (see §2)

```

---

## 12) Security & Privacy

* No telemetry.
* API keys remain local (optional future encryption).
* Provider responses stored locally for audit.
* Rule sets and overrides are local unless exported by the user.

---

## 13) Development & Run

```
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run GUI:

```
python -m marketlens.gui
```

Run Scheduler:

```
python -m marketlens.scheduler
```

---

## 14) Roadmap Highlights

* **Phase 1:** Collector + DuckDB + FMP; derived views; rule engine v1; VS-style dock layout.
* **Phase 2:** Postgres backend + MVs; multiple providers with resolver priorities.
* **Phase 3:** Plugin ecosystem (filters, indicators, rule libraries, UI panels).
* **Phase 4:** Packaging (PyInstaller) & community templates.

---

### Summary

* **PyQt6 dynamic UI** with VS2022/Rider-style docking (main work area, explorer side panel, properties panel).
* **GUI and Scheduler** share one **data-collection library**; users can automate or run manually.
* **Providers are pluggable**, with capability discovery; **facts are persisted** with provenance; **metrics & categories are computed** in views and rules.
* **User-defined categorization** is first-class, importable/exportable, and plugin-extensible.
