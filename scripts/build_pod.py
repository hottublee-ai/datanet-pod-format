#!/usr/bin/env python3
"""
Datanet Pod Builder — template script for building v2 format pods.

Given your trading data (trades, signals, scans), this script produces
Pod A and/or Pod B JSON files ready to pin to IPFS and submit to Reppo.

Usage:
    python3 build_pod.py --trades trades.jsonl --output ./pods
    python3 build_pod.py --trades trades.jsonl --signals signals.jsonl --scans scans.jsonl --output ./pods --analytics analytics.json

File formats:
    trades.jsonl  — Line-delimited JSON. Each line has {"type":"open"|"close", ...}
    signals.jsonl — Line-delimited JSON of signal evaluations (near-misses, blocked entries)
    scans.jsonl   — Line-delimited JSON of market scan snapshots
"""

import json
import os
import argparse
from pathlib import Path
from datetime import datetime, timezone

VERSION = "2.0"


def load_jsonl(path):
    """Load a line-delimited JSON file into a list of dicts."""
    records = []
    if not Path(path).exists():
        print(f"  Warning: {path} not found, skipping")
        return records
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"  Warning: skipping malformed line in {path}: {e}")
    return records


def build_pod_a(trades_path: str, analytics_path: str) -> dict:
    """Build Pod A — Execution and Learning."""
    raw = load_jsonl(trades_path)
    analytics = load_jsonl(analytics_path)

    opens = [r for r in raw if r.get("type") == "open"]
    closes = [r for r in raw if r.get("type") == "close"]

    completed = []
    for c in closes:
        coin = c["coin"]
        # Find the most recent open before this close
        entry = next((r for r in reversed(opens) if r["coin"] == coin and r["ts"] < c["ts"]), {})
        completed.append({
            "coin": coin,
            "direction": c.get("direction", "LONG"),
            "entry_price": c.get("entry_px", entry.get("entry_px", 0)),
            "exit_price": c.get("exit_px", 0),
            "size": c.get("size", entry.get("size", 0)),
            "leverage": entry.get("leverage", 0),
            "entry_score": entry.get("entry_score", 0),
            "pnl_usd": round(c.get("pnl_usd", 0), 2),
            "pnl_pct": round(c.get("pnl_pct", 0), 2),
            "hold_hours": c.get("hold_hours", 0),
            "exit_reason": c.get("exit_reason", ""),
            "entry_reasons": entry.get("entry_reasons", []),
        })

    # Open positions (coins with opens but no matching close)
    close_coins = {c["coin"] for c in closes}
    open_positions = []
    seen = {}
    for r in sorted(opens, key=lambda x: x["ts"]):
        seen[r["coin"]] = r
    for coin, r in seen.items():
        if coin not in close_coins:
            open_positions.append({
                "coin": coin,
                "direction": r.get("direction", "LONG"),
                "entry_price": r.get("entry_px"),
                "size": r.get("size"),
                "leverage": r.get("leverage"),
                "entry_score": r.get("entry_score"),
                "entry_reasons": r.get("entry_reasons", []),
                "opened_at": r.get("dt"),
            })

    # Compute summary
    total_pnl = round(sum(t["pnl_usd"] for t in completed), 2)
    wins = len([t for t in completed if t["pnl_usd"] > 0])
    total = len(completed)
    wr = round(wins / total * 100, 1) if total else 0

    # Determine data period
    all_ts = [r["ts"] for r in raw if r.get("ts")]
    ds = datetime.fromtimestamp(min(all_ts), timezone.utc).strftime("%Y-%m-%d") if all_ts else "unknown"
    de = datetime.fromtimestamp(max(all_ts), timezone.utc).strftime("%Y-%m-%d") if all_ts else "unknown"

    return {
        "format_version": VERSION,
        "metadata": {
            "pod_type": "A",
            "title": "Execution and Learning",
            "agent": os.environ.get("AGENT_NAME", "YourBot"),
            "agent_id": os.environ.get("AGENT_ID", ""),
            "exchange": os.environ.get("EXCHANGE", "Hyperliquid"),
            "strategy": os.environ.get("STRATEGY_DESC", "Describe your strategy here"),
            "data_format_version": VERSION,
            "data_period": f"{ds} to {de}",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "record_counts": {
                "completed_trades": total,
                "open_positions": len(open_positions),
                "analytics_reports": len(analytics),
            },
            "summary": {
                "total_pnl_usd": total_pnl,
                "win_rate_pct": wr,
                "wins": wins,
                "losses": total - wins,
            },
        },
        "trades": {
            "completed": completed,
            "open": open_positions,
        },
        "performance_analytics": analytics,
    }


def build_pod_b(signals_path: str, scans_path: str) -> dict:
    """Build Pod B — Signal Intelligence."""
    signals = load_jsonl(signals_path)
    scans = load_jsonl(scans_path)

    blocked = [r for r in signals if r.get("direction") == "BLOCKED"]
    filtered = [r for r in signals if r.get("direction") == "FILTERED"]
    near_miss = [r for r in signals if r.get("direction") in ("NEAR_MISS", "NONE")]

    def compact(r):
        return {
            "ts": r.get("ts"),
            "dt": r.get("dt"),
            "coin": r.get("coin"),
            "score": r.get("score"),
            "price": r.get("price"),
            "note": r.get("note", "") if r.get("note") else None,
        }

    # Compact scans — keep last 50 for size management
    scans = scans[-50:] if len(scans) > 50 else scans
    market_scans = []
    all_coins = set()
    for s in scans:
        coins = {}
        for coin, info in s.get("coins", {}).items():
            coins[coin] = {
                "score": info.get("score"),
                "signal": info.get("signal"),
                "price": info.get("price"),
            }
            all_coins.add(coin)
        market_scans.append({
            "ts": s.get("ts"),
            "dt": s.get("dt"),
            "equity": s.get("equity"),
            "coins": coins,
        })

    # Determine data period
    all_ts = [r["ts"] for r in signals if r.get("ts")] + [r["ts"] for r in scans if r.get("ts")]
    ds = datetime.fromtimestamp(min(all_ts), timezone.utc).strftime("%Y-%m-%d") if all_ts else "unknown"
    de = datetime.fromtimestamp(max(all_ts), timezone.utc).strftime("%Y-%m-%d") if all_ts else "unknown"

    return {
        "format_version": VERSION,
        "metadata": {
            "pod_type": "B",
            "title": "Signal Intelligence",
            "agent": os.environ.get("AGENT_NAME", "YourBot"),
            "agent_id": os.environ.get("AGENT_ID", ""),
            "exchange": os.environ.get("EXCHANGE", "Hyperliquid"),
            "data_format_version": VERSION,
            "data_period": f"{ds} to {de}",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "signal_categories": {
                "blocked_entries": len(blocked),
                "filtered_signals": len(filtered),
                "near_misses": len(near_miss),
            },
            "market_scans": {
                "count": len(market_scans),
                "coins_monitored": len(all_coins),
            },
        },
        "near_misses": {
            "blocked_entries": [compact(r) for r in blocked],
            "filtered_signals": [compact(r) for r in filtered],
            "near_misses": [compact(r) for r in near_miss],
        },
        "market_scans": market_scans,
    }


def main():
    parser = argparse.ArgumentParser(description="Build trading data pods for the datanet")
    parser.add_argument("--trades", help="Path to trades.jsonl (opens + closes)")
    parser.add_argument("--analytics", help="Path to performance analytics JSONL")
    parser.add_argument("--signals", help="Path to signal evaluations JSONL")
    parser.add_argument("--scans", help="Path to market scan snapshots JSONL")
    parser.add_argument("--output", "-o", default="./pods", help="Output directory")
    parser.add_argument("--pod-a", action="store_true", help="Build Pod A only")
    parser.add_argument("--pod-b", action="store_true", help="Build Pod B only")
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    build_a = args.pod_a or not (args.pod_b)
    build_b = args.pod_b or not (args.pod_a)

    if build_a:
        if not args.trades:
            print("Error: --trades required for Pod A")
            return
        print("Building Pod A (Execution and Learning)...")
        pod_a = build_pod_a(args.trades, args.analytics or "")
        path = out / "pod_a.json"
        with open(path, "w") as f:
            json.dump(pod_a, f, indent=2)
        print(f"  Saved to {path}")
        print(f"  {pod_a['metadata']['record_counts']['completed_trades']} completed trades")
        print()

    if build_b:
        if not args.signals and not args.scans:
            print("Warning: --signals and/or --scans recommended for Pod B")
        print("Building Pod B (Signal Intelligence)...")
        pod_b = build_pod_b(args.signals or "", args.scans or "")
        path = out / "pod_b.json"
        with open(path, "w") as f:
            json.dump(pod_b, f, indent=2)
        print(f"  Saved to {path}")
        cats = pod_b["metadata"]["signal_categories"]
        print(f"  {cats['blocked_entries']} blocked, {cats['filtered_signals']} filtered, {cats['near_misses']} near-misses")
        print(f"  {pod_b['metadata']['market_scans']['count']} market scans")
        print()

    print("Done! Pin the JSON files to IPFS and submit on Reppo.")
    print("  Pinata:  curl -X POST https://api.pinata.cloud/pinning/pinJSONToIPFS \\")
    print("             -H \"Authorization: Bearer YOUR_JWT\" \\")
    print(f"             -d @{out / 'pod_a.json'}")


if __name__ == "__main__":
    main()