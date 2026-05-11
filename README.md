# Datanet Pod Format v2

[![TradingGym AI on Reppo](https://img.shields.io/badge/Reppo-TradingGym%20AI%20Subnet-blue?style=flat-square)](https://reppo.ai/subnets/cmnhuowns000bic04e16t6735)

**An open standard for structuring and submitting trading data pods to prediction markets on [Reppo](https://reppo.ai).**

Built for the TradingGym AI datanet. Running live on [DegenClaw](https://degen.virtuals.io) agents in the Virtuals competition.

---

## Why contribute to TradingGym AI?

Your trading bot is already generating structured data — entries, exits, scores, signals, near-misses. Most bots throw this data away. This pipeline captures it, structures it into verifiable IPFS pods, and submits them to TradingGym AI on Reppo — where you earn emissions for quality contributions.

**The flywheel:**

Better training data → better trading models → better-performing agents → more verifiable on-chain performance → higher-quality data.

Every pod you publish feeds that loop. You earn REPPO rewards for quality contributions, and the models trained on your data improve the whole ecosystem — including your own agents.

**If you're already running a bot, you're already generating this data. The only question is whether it gets captured or thrown away.**

---

## How it works

```
Your Bot ──► PodLogger ──► trades.jsonl ──► build_pod.py ──► Pod A (Execution)
                │           signals.jsonl ──►                ──► Pod B (Signals)
                └── 3 calls ─► scans.jsonl  ──►                 │
                                                                 │
                                                   Pin to IPFS ◄─┘
                                                         │
                                              Submit on Reppo ◄─┘
                                                         │
                                              Earn REPPO rewards
```

Three logging calls in your bot. One script to build pods. Pin to IPFS and submit.

---

## How Reppo works

Reppo is a **prediction market for data quality** — not a data marketplace. Data quality is determined by staking markets:

1. **Submit** — Raw data flows in as pods
2. **Stake** — Domain experts put REPPO on quality judgments
3. **Settle** — Markets close every 48 hours. Accurate evaluators earn. Wrong calls lose their stake
4. **Deliver** — Surviving data ships to subscribed AI teams as living data feeds

Your pod earns emissions when it passes quality markets. The better your data, the more REPPO you earn.

---

## Quick Start (15 minutes)

### 1. Add PodLogger to your bot

Copy [`examples/logger_example.py`](examples/logger_example.py) into your project. Then add 3 logging calls:

```python
from logger_example import PodLogger

log = PodLogger(agent_name="MyBot", data_dir="./data")

# When you open a trade:
log.log_open("BTC", 81500.0, 0.001, 5, 8.0, ["RSI oversold", "EMA crossover"])

# When a signal is evaluated but not traded (near-miss):
log.log_signal("ETH", 2350.0, 4.5, "NONE", ["RSI too high at 68"])

# When you close a trade:
log.log_close("BTC", 82300.0, 81500.0, 0.001, 0.80, 6.5, "TP_HIT")
```

That's it. The logger writes flat JSONL files — no database, no config, no cloud service.

### 2. Build pods from your data

```bash
git clone https://github.com/hottublee-ai/datanet-pod-format
cd datanet-pod-format

python3 scripts/build_pod.py \
  --trades /path/to/trades.jsonl \
  --signals /path/to/signals.jsonl \
  --scans /path/to/scans.jsonl \
  --output ./my_pods
```

### 3. Pin to IPFS (free via Pinata)

```bash
curl -X POST https://api.pinata.cloud/pinning/pinJSONToIPFS \
  -H "Authorization: Bearer YOUR_JWT" \
  -d @./my_pods/pod_a.json
```

### 4. Submit on Reppo

Go to [reppo.ai](https://reppo.ai) → Publish a Pod → paste your IPFS gateway URL.

**Cost: free. Setup: ~15 minutes.**

---

## Pod Types

| Pod | Content | Best For |
|-----|---------|----------|
| **A** — Execution & Learning | Completed trades + performance analytics | Proving strategy execution quality |
| **B** — Signal Intelligence | Near-misses, blocked entries, market scans | Demonstrating signal coverage and market awareness |

### Why near-misses matter

T2 data captures your bot's decision boundary — what it *almost* traded and why it didn't. That counterfactual signal is extremely rare and highly valuable for training. Most bots never log it. This format does.

---

## Spec

Full format specification: [SPEC.md](SPEC.md)

### Examples

- [Pod A — Execution & Learning](examples/pod_a_example.json) — 12 completed trades with performance analytics
- [Pod B — Signal Intelligence](examples/pod_b_example.json) — Near-misses, blocked entries, and market scans
- [Logger Example](examples/logger_example.py) — Drop-in Python logger for your bot

### What you need

- A trading bot (any exchange, any language)
- A free [Pinata](https://pinata.cloud) account for IPFS pinning
- A wallet to submit pods to TradingGym AI on Reppo

### Submitting

1. Build your pod JSON following the spec
2. Pin it to IPFS (Pinata, web3.storage, lighthouse, etc.)
3. Copy the IPFS gateway URL
4. Go to [reppo.ai](https://reppo.ai) → Publish a Pod
5. Fill in name (50 chars max), description (200 chars max), and the IPFS link
6. Add a thumbnail (PNG/JPG, under 2MB) — highly recommended

Pods last 3-4 epochs (~6-8 days). Republish with fresh data to keep them active.

---

## Live Example

This format is running live on agents competing in the Virtuals DegenClaw $100K competition. On-chain trade history is fully verifiable — anyone can cross-reference pod data against Hyperliquid.

Check the [TradingGym AI datanet on Reppo](https://reppo.ai/subnets/cmnhuowns000bic04e16t6735) for live submissions.

---

## Contributing

PRs welcome. If you're running a bot and want to plug into the datanet, open an issue — happy to help you get wired up.

---

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

*Built on [Reppo](https://reppo.ai) × [Virtuals Protocol](https://virtuals.io)*