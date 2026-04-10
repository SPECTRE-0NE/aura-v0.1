-- Sample schema creation script (mirrors storage.py)
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS markets (
    market_id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    slug TEXT NOT NULL,
    expiry_ts TEXT,
    strike REAL,
    is_active INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS token_pairs (
    market_id TEXT NOT NULL,
    yes_token_id TEXT NOT NULL,
    no_token_id TEXT NOT NULL,
    PRIMARY KEY (market_id, yes_token_id, no_token_id)
);

CREATE TABLE IF NOT EXISTS orderbook_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    token_id TEXT NOT NULL,
    best_bid_price REAL,
    best_bid_size REAL,
    best_ask_price REAL,
    best_ask_size REAL,
    bids_json TEXT,
    asks_json TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS btc_ticks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    source TEXT
);

CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_start TEXT NOT NULL,
    ts_end TEXT NOT NULL,
    market_id TEXT NOT NULL,
    yes_token_id TEXT NOT NULL,
    no_token_id TEXT NOT NULL,
    gross_edge REAL NOT NULL,
    net_edge REAL NOT NULL,
    executable INTEGER NOT NULL,
    fee_cost REAL NOT NULL,
    slippage_cost REAL NOT NULL,
    latency_cost REAL NOT NULL,
    btc_price REAL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS simulated_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    market_id TEXT NOT NULL,
    side TEXT NOT NULL,
    qty REAL NOT NULL,
    expected_price REAL NOT NULL,
    expected_pnl REAL NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS run_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    config_json TEXT NOT NULL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_markets_market_id ON markets(market_id);
CREATE INDEX IF NOT EXISTS idx_token_pairs_market_id ON token_pairs(market_id);
CREATE INDEX IF NOT EXISTS idx_orderbook_token_ts ON orderbook_snapshots(token_id, ts);
CREATE INDEX IF NOT EXISTS idx_btc_ticks_ts ON btc_ticks(ts);
CREATE INDEX IF NOT EXISTS idx_opp_market_ts ON opportunities(market_id, ts_start);
