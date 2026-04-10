# polymarket-arb-research

Research-only tooling for recording Polymarket BTC short-duration binary markets and replaying historical data to evaluate complementary arbitrage feasibility.

> This is **not** a live trading bot. It intentionally excludes private keys, wallet management, signed order placement, and live execution.

## What this project does

For each BTC market with YES/NO tokens, the system records:
- market metadata (question, expiry, token IDs)
- YES and NO order book snapshots
- external BTC reference ticks

Then it replays data and tests conservative execution assumptions for:

```text
yes_ask + no_ask + fees + slippage + latency_cost < 1.00
```

Only windows that survive latency and pass size checks are marked executable.

## Project layout

```text
polymarket-arb-research/
  README.md
  requirements.txt
  .env.example
  config.py
  main.py
  market_discovery.py
  book_recorder.py
  btc_price_feed.py
  storage.py
  models.py
  edge_logic.py
  replay_backtest.py
  opportunity_report.py
  utils.py
  tests/test_edge_logic.py
  logs/
  data/raw/
  data/processed/
```

## Setup

1. Create and activate a Python 3.11+ environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy env template:
   ```bash
   cp .env.example .env
   ```
4. Adjust `.env` values as needed.

## CLI usage

### Record data

```bash
python main.py record --duration 7200 --db-path ./data/processed/polymarket_arb.sqlite3 --market-refresh-interval 300
```

### Run replay backtest

```bash
python main.py backtest --db-path ./data/processed/polymarket_arb.sqlite3 --fee-rate 0.02 --slippage-buffer 0.005 --latency-ms 250 --min-trade-size 25
```

### Generate report + CSV

```bash
python main.py report --db-path ./data/processed/polymarket_arb.sqlite3 --csv-out ./data/processed/opportunities.csv --top-n 20
```

Use `--include-non-executable` only when you explicitly want to inspect failures; default report mode is conservative and filters to executable rows.

## SQLite schema (v1)

Schema is created automatically by `Storage.init()`. Core tables:
- `markets`
- `token_pairs`
- `orderbook_snapshots`
- `btc_ticks`
- `opportunities`
- `simulated_trades`
- `run_metadata`

Key indexes include `(market_id)`, `(token_id, ts)`, and `ts` indexes for fast replay scans.

## Example CSV output format

```csv
ts_start,ts_end,market_id,gross_edge,net_edge,executable,btc_price,notes
2026-04-10T12:00:00.000Z,2026-04-10T12:00:00.250Z,12345,0.012000,0.003500,1,82110.11,executable
```

## Design notes

- Async-first approach for long-running recorders.
- SQLite write batching and persistent DB connection for better throughput.
- Conservative backtest assumptions (fees, slippage, latency, one-leg fill risk).
- UTC timestamps end-to-end with normalized `Z` format.
- Pure edge-detection functions (`edge_logic.py`) are unit-testable.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Future extension points

- `main.py` includes TODO marker where live execution orchestrator could be added later.
- `replay_backtest.py` is structured so additional execution/risk models can be plugged in.
- `storage.py` can be upgraded to Postgres without changing upper-layer interfaces.
