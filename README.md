# Datanet Pod Format v2

An open standard for structuring and submitting trading data bundles ("pods") to prediction markets on [Reppo](https://reppo.ai). Built for the HotTubLee AI datanet.

## Why This Exists

Trading bots generate mountains of structured data — executed trades, signal decisions, market scans. This data is valuable for training AI models, but only if it's in a consistent, machine-readable format.

This spec defines how to package that data into **pods**: lightweight, self-describing JSON bundles that anyone can submit to earn emissions on Reppo.

## Quick Start

```bash
# Clone this repo
git clone https://github.com/hottublee-ai/datanet-pod-format

# Use the template script to build your own pods
python3 scripts/build_pod.py --trades trades.jsonl --output my_pod.json

# Pin to IPFS (Pinata, web3.storage, etc.)
curl -X POST https://api.pinata.cloud/pinning/pinJSONToIPFS \
  -H "Authorization: Bearer YOUR_JWT" \
  -d @my_pod.json

# Submit the IPFS gateway URL on Reppo
```

## Pod Types

| Pod | Content | Best For |
|-----|---------|----------|
| **A** — Execution & Learning | Completed trades + performance analytics | Proving strategy execution quality |
| **B** — Signal Intelligence | Near-misses, blocked entries, market scans | Demonstrating signal coverage and market awareness |

## Spec

Full format specification: [SPEC.md](SPEC.md)

## Examples

- [Pod A — Execution & Learning](examples/pod_a_example.json)
- [Pod B — Signal Intelligence](examples/pod_b_example.json)

## Submitting

1. Build your pod JSON following the spec
2. Pin it to IPFS (Pinata, web3.storage, lighthouse, etc.)
3. Copy the IPFS gateway URL
4. Go to [reppo.ai](https://reppo.ai) → Publish a Pod
5. Fill in name (50 chars max), description (200 chars max), and the IPFS link
6. Add a thumbnail (PNG/JPG, under 2MB) — highly recommended

Pods last 3-4 epochs (~6-8 days). Republish with fresh data to keep them active.

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).