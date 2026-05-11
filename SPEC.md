# Datanet Pod Format Specification v2.0

## Overview

A pod is a JSON document containing structured trading data, pinned to IPFS and submitted to Reppo for verification and emissions. This spec defines the schema for both pod types.

---

## Common Structure

Every pod has this top-level structure:

```json
{
  "format_version": "2.0",
  "metadata": { ... },
  "<data_section>": { ... }
}
```

### `format_version`

String. The version of this spec the pod conforms to. Currently `"2.0"`.

### `metadata`

Object. Self-describing metadata about the pod and its data. Required fields:

| Field | Type | Description |
|-------|------|-------------|
| `pod_type` | string | `"A"` or `"B"` |
| `title` | string | Human-readable title (e.g., `"Execution and Learning"`) |
| `agent` | string | Name of the trading agent or bot |
| `agent_id` | string | Unique identifier for the agent (optional) |
| `exchange` | string | Exchange name (e.g., `"Hyperliquid"`, `"Binance"`, `"dYdX"`) |
| `data_format_version` | string | Must match `format_version` |
| `data_period` | string | Date range, format `"YYYY-MM-DD to YYYY-MM-DD"` |
| `built_at` | string | ISO 8601 timestamp of when the pod was built |
| `record_counts` | object | Per-section record counts (varies by pod type) |

---

## Pod A — Execution & Learning

### Purpose

Contains **completed trades** (T1) with full entry/exit data and **performance analytics** (T4) summarizing trade quality and strategy insights.

### Schema

```json
{
  "format_version": "2.0",
  "metadata": {
    "pod_type": "A",
    "title": "Execution and Learning",
    "agent": "MyBot",
    "agent_id": "123",
    "exchange": "Hyperliquid",
    "strategy": "Brief strategy description — timeframe, entry rules, exits, position limits",
    "data_format_version": "2.0",
    "data_period": "2026-05-06 to 2026-05-10",
    "built_at": "2026-05-11T00:00:00Z",
    "record_counts": {
      "completed_trades": 12,
      "open_positions": 3,
      "analytics_reports": 1
    },
    "summary": {
      "total_pnl_usd": 3.40,
      "win_rate_pct": 41.7,
      "wins": 5,
      "losses": 7
    }
  },
  "trades": {
    "completed": [ ... ],
    "open": [ ... ]
  },
  "performance_analytics": [ ... ]
}
```

### `trades.completed`

Array of completed trade objects. Each trade:

| Field | Type | Description |
|-------|------|-------------|
| `coin` | string | Trading pair or asset (e.g., `"BTC"`, `"ETH"`) |
| `direction` | string | `"LONG"` or `"SHORT"` |
| `entry_price` | number | Entry price |
| `exit_price` | number | Exit price |
| `size` | number | Position size in base units |
| `leverage` | number | Leverage used |
| `entry_score` | number | Signal score at entry (0-10 scale) |
| `pnl_usd` | number | Realized P&L in USD |
| `pnl_pct` | number | Realized P&L as percentage of position value |
| `hold_hours` | number | Duration of the trade in hours |
| `exit_reason` | string | Reason for exit (`"TP_HIT"`, `"TIME_STOP"`, `"TRAILING_STOP"`, etc.) |
| `entry_reasons` | array of strings | Signal triggers that led to entry (optional) |

### `trades.open`

Array of open position objects. Same fields as completed trades, but without exit data:

| Field | Type |
|-------|------|
| `coin` | string |
| `direction` | string |
| `entry_price` | number |
| `size` | number |
| `leverage` | number |
| `entry_score` | number |
| `entry_reasons` | array (optional) |
| `opened_at` | string (ISO 8601) |

### `performance_analytics`

Array of analysis report objects. Each report contains summary metrics derived from the trade data. Schema is flexible — common fields include:

| Field | Type | Description |
|-------|------|-------------|
| `n_trades` | number | Number of trades analyzed |
| `win_rate` | number | Win rate as percentage |
| `total_pnl_usd` | number | Aggregate P&L |
| `avg_pnl_pct` | number | Average return per trade |
| `exit_stats` | object | Breakdown of exits by type (TP, time stop, trail), with counts and avg P&L |
| `score_map` | object | Average P&L by entry score tier |
| `time_stop_tuning` | object | Analysis of time-stop effectiveness |

---

## Pod B — Signal Intelligence

### Purpose

Contains **near-miss signals** (T2) — decisions the bot evaluated but didn't execute — and **market scan snapshots** (T3) showing the full market state at regular intervals.

### Schema

```json
{
  "format_version": "2.0",
  "metadata": {
    "pod_type": "B",
    "title": "Signal Intelligence",
    "agent": "MyBot",
    "agent_id": "123",
    "exchange": "Hyperliquid",
    "data_format_version": "2.0",
    "data_period": "2026-05-06 to 2026-05-10",
    "built_at": "2026-05-11T00:00:00Z",
    "signal_categories": {
      "blocked_entries": 414,
      "filtered_signals": 221,
      "near_misses": 1214
    },
    "market_scans": {
      "count": 50,
      "coins_monitored": 17
    }
  },
  "near_misses": {
    "blocked_entries": [ ... ],
    "filtered_signals": [ ... ],
    "near_misses": [ ... ]
  },
  "market_scans": [ ... ]
}
```

### Signal Categories

T2 signals are grouped into three categories:

#### `blocked_entries`

Signals that scored >= the entry threshold AND generated a LONG/SHORT signal, but **could not execute** because position limits were reached.

| Field | Type | Description |
|-------|------|-------------|
| `ts` | number | Unix timestamp |
| `dt` | string | ISO 8601 datetime |
| `coin` | string | Asset |
| `score` | number | Signal score |
| `price` | number | Asset price at time of evaluation |
| `note` | string (optional) | Context about why blocked (e.g., `"max_pos=5, open=5"`) |

#### `filtered_signals`

Signals that scored >= the entry threshold and had a LONG/SHORT direction, but were **filtered by secondary checks** (pullback distance, size constraints, etc.) despite having open slots.

Same fields as `blocked_entries`.

#### `near_misses`

Signals that scored **just below the entry threshold** (e.g., 4.0–4.9 on a 5.0 gate), indicating the bot was close to entering.

Same fields as above, minus `note`.

### `market_scans`

Array of market scan snapshots. Each scan captures the state of all monitored coins at a single point in time:

```json
{
  "ts": 1778456425,
  "dt": "2026-05-10T23:40:25Z",
  "equity": 217.57,
  "coins": {
    "BTC": { "score": 9.0, "signal": "LONG", "price": 80834.0 },
    "ETH": { "score": 7.0, "signal": "LONG", "price": 2330.0 },
    "SOL": { "score": 8.0, "signal": "LONG", "price": 94.96 }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ts` | number | Unix timestamp |
| `dt` | string | ISO 8601 datetime |
| `equity` | number | Account equity at time of scan |
| `coins` | object | Map of coin → `{ score, signal, price }` |

Keep scans compact by excluding verbose `reasons` arrays in market scan data — they bulk up the file without adding signal-level value.

---

## Data Period

The `data_period` field in metadata must cover the range of the earliest to latest record timestamps across all data sections. This allows consumers to quickly assess recency without parsing the full dataset.

## Versioning

This spec follows semantic versioning. Breaking changes (field removals, required field additions, structural changes) increment the major version. Additive changes (new optional fields, new sections) increment the minor version.

Current version: **2.0**

## See Also

- [README.md](README.md) — overview and quick start
- [examples/pod_a_example.json](examples/pod_a_example.json) — full Pod A example
- [examples/pod_b_example.json](examples/pod_b_example.json) — full Pod B example
- [scripts/build_pod.py](scripts/build_pod.py) — template builder script