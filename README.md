# MarketLens

**An open, private, extensible platform for serious stock analysis — built together.**

---

## Overview

MarketLens is a **local-first, desktop-first stock analysis platform** built with **PyQt6**.  
It is **not a trading bot** — instead, it focuses on **breakout detection**, **fundamental analysis**, and **user-defined categorization** — all performed locally on the user’s machine.

MarketLens combines a **dynamic PyQt6 GUI** and a **background scheduler** that both use the same data-collection engine.  
All data, API keys, and configurations stay private — nothing is sent to the cloud.

---

## Core Highlights

- 🧠 **PyQt6 GUI** – Dynamic VS2022/Rider-style interface with dockable panels and persistent layouts.  
- ⚙️ **Shared Engine** – GUI and Scheduler share one data-collection library.  
- 🗃️ **Multi-Database** – DuckDB (embedded) or Postgres (multi-process; optional TimescaleDB).  
- 🔌 **Multi-Provider** – Pluggable adapters for FMP, Polygon, Finnhub, and EDGAR.  
- 🧩 **Plugin System** – Extend with filters, indicators, charts, and rule sets.  
- 🏷️ **Rule-Based Categorization** – Define your own company groupings (e.g., “export-heavy,” “commodity producers,” “low-debt tech”).  
- 🔒 **Local & Private** – No telemetry, no cloud backend; data and keys stay on your machine.

---

## Quick Start

> MarketLens is currently in **early development**.  
