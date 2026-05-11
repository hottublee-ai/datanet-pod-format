#!/usr/bin/env python3
"""
PodLogger — Instrument your bot to produce datanet-ready JSONL files.

Drop this into your trading bot and call the 3 logging methods.
It writes flat JSONL files that feed directly into build_pod.py.

Usage:
    logger = PodLogger(agent_name="MyBot", data_dir="./data")
    
    # When you open a trade:
    logger.log_open(coin="BTC", price=81500.0, size=0.001, leverage=5,
                    score=8.0, reasons=["RSI oversold", "EMA crossover"])
    
    # When a signal is evaluated but not traded:
    logger.log_signal(coin="ETH", price=2350.0, score=4.5,
                      direction="NONE", reasons=["RSI too high"])
    
    # When you close a trade:
    logger.log_close(coin="BTC", exit_price=82300.0, entry_price=81500.0,
                     size=0.001, pnl_usd=0.80, hold_hours=6.5,
                     exit_reason="TP_HIT", entry_score=8.0,
                     entry_reasons=["RSI oversold", "EMA crossover"])
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


class PodLogger:
    """Logs trading events to JSONL files for the datanet pod builder."""

    def __init__(self, agent_name: str = "MyBot", data_dir: str = "./data"):
        self.agent_name = agent_name
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Output files
        self.trades_file = self.data_dir / "trades.jsonl"
        self.signals_file = self.data_dir / "signals.jsonl"
        self.scans_file = self.data_dir / "scans.jsonl"

    def _ts(self) -> tuple:
        """Return (unix_timestamp, iso_datetime) in UTC."""
        now = datetime.now(timezone.utc)
        return now.timestamp(), now.isoformat()

    def log_open(self, coin: str, price: float, size: float, leverage: int,
                 score: float, reasons: list, direction: str = "LONG",
                 sl_price: float = None, tp_price: float = None):
        """
        Call when you open a position.

        Fields are written to the JSONL line exactly as shown below.
        See examples/pod_a_example.json for the full expected format.
        """
        ts, dt = self._ts()
        record = {
            "type": "open",
            "ts": ts,
            "dt": dt,
            "coin": coin.upper(),
            "direction": direction,
            "entry_px": price,
            "size": size,
            "leverage": leverage,
            "entry_score": round(score, 1),
            "entry_reasons": reasons,
        }
        if sl_price is not None:
            record["sl_price"] = sl_price
        if tp_price is not None:
            record["tp_price"] = tp_price

        with open(self.trades_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def log_close(self, coin: str, exit_price: float, entry_price: float,
                  size: float, pnl_usd: float, hold_hours: float,
                  exit_reason: str, leverage: int = None,
                  entry_score: float = None, entry_reasons: list = None,
                  pnl_pct: float = None, direction: str = "LONG"):
        """
        Call when a position closes.

        The build_pod.py script pairs closes with their corresponding
        open records by matching coin name and timestamp order.
        """
        ts, dt = self._ts()
        record = {
            "type": "close",
            "ts": ts,
            "dt": dt,
            "coin": coin.upper(),
            "direction": direction,
            "entry_px": entry_price,
            "exit_px": exit_price,
            "size": size,
            "pnl_usd": round(pnl_usd, 2),
            "pnl_pct": round(pnl_pct, 4) if pnl_pct else round((exit_price / entry_price - 1) * 100 * (leverage or 1), 2),
            "hold_hours": round(hold_hours, 2),
            "exit_reason": exit_reason,
        }
        if entry_score is not None:
            record["entry_score"] = round(entry_score, 1)
        if entry_reasons is not None:
            record["entry_reasons"] = entry_reasons
        if leverage is not None:
            record["leverage"] = leverage

        with open(self.trades_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def log_signal(self, coin: str, price: float, score: float,
                   direction: str = "NONE", reasons: list = None,
                   note: str = None):
        """
        Call when a signal is evaluated but NOT traded.

        direction should be one of:
        - "NONE" — score below threshold, passed over
        - "BLOCKED" — scored well but blocked (slots full, cooldown, etc.)
        - "FILTERED" — failed a pre-trade filter

        These become the 'near_misses', 'blocked_entries', and
        'filtered_signals' sections in Pod B.
        """
        ts, dt = self._ts()
        record = {
            "ts": ts,
            "dt": dt,
            "coin": coin.upper(),
            "direction": direction,
            "score": round(score, 1),
            "price": price,
            "reasons": reasons or [],
        }
        if note:
            record["note"] = note

        with open(self.signals_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def log_scan(self, equity: float, coins: dict):
        """
        Call after each full market scan cycle.

        coins expects { "BTC": {"score": 8.0, "signal": "LONG", "price": 81500}, ... }
        This provides market context for Pod B.
        """
        ts, dt = self._ts()
        record = {
            "ts": ts,
            "dt": dt,
            "equity": round(equity, 2),
            "coins": coins,
        }

        with open(self.scans_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        return record


# ── Self-test: run this file to see example output ──────────────────────────
if __name__ == "__main__":
    log = PodLogger(agent_name="ExampleBot", data_dir="/tmp/datanet_example")
    
    # Simulate a trading session
    log.log_open("BTC", 81500.0, 0.001, 5, 8.0, ["RSI oversold", "EMA crossover"])
    log.log_signal("ETH", 2350.0, 4.5, "NONE", ["RSI too high at 68"])
    log.log_open("SOL", 142.0, 0.5, 5, 6.5, ["Volume spike", "Support bounce"])
    log.log_signal("DOGE", 0.112, 4.9, "NONE", ["RSI borderline at 66.5"])
    log.log_signal("LINK", 14.5, 9.0, "BLOCKED", ["Score 9.0 but max positions reached"], 
                   note="3 slots full")
    log.log_close("BTC", 82300.0, 81500.0, 0.001, 0.80, 6.5,
                  "TP_HIT", leverage=5, entry_score=8.0,
                  entry_reasons=["RSI oversold", "EMA crossover"])
    log.log_scan(1000.0, {
        "BTC": {"score": 7.0, "signal": "HOLD", "price": 82200.0},
        "ETH": {"score": 4.5, "signal": "NONE", "price": 2340.0},
        "SOL": {"score": 6.5, "signal": "LONG", "price": 143.5},
    })

    print(f"Example data written to /tmp/datanet_example/")
    print(f"  trades.jsonl — {sum(1 for _ in open('/tmp/datanet_example/trades.jsonl'))} records")
    print(f"  signals.jsonl — {sum(1 for _ in open('/tmp/datanet_example/signals.jsonl'))} records")
    print(f"  scans.jsonl — {sum(1 for _ in open('/tmp/datanet_example/scans.jsonl'))} records")
    print()
    print("Now build pods:")
    print("  python3 scripts/build_pod.py --trades /tmp/datanet_example/trades.jsonl \\")
    print("    --signals /tmp/datanet_example/signals.jsonl \\")
    print("    --scans /tmp/datanet_example/scans.jsonl --output ./mypods")