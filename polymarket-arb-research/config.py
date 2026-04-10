from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    db_path: str = "./data/processed/polymarket_arb.sqlite3"
    log_level: str = "INFO"

    polymarket_gamma_url: str = "https://gamma-api.polymarket.com"
    polymarket_clob_url: str = "https://clob.polymarket.com"

    market_refresh_seconds: int = 300
    orderbook_poll_seconds: float = 1.0
    stale_feed_seconds: int = 15
    orderbook_top_levels: int = 5

    btc_ws_url: str = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    btc_symbol: str = "BTCUSDT"

    fee_rate: float = 0.02
    slippage_buffer: float = 0.005
    latency_ms: int = 250
    min_trade_size: float = 25.0
    max_book_skew_ms: int = 300
    one_leg_fill_risk: float = 0.15


def load_settings() -> Settings:
    load_dotenv()
    defaults = Settings()
    settings = Settings(
        db_path=os.getenv("PM_DB_PATH", defaults.db_path),
        log_level=os.getenv("LOG_LEVEL", defaults.log_level),
        polymarket_gamma_url=os.getenv("POLYMARKET_GAMMA_URL", defaults.polymarket_gamma_url),
        polymarket_clob_url=os.getenv("POLYMARKET_CLOB_URL", defaults.polymarket_clob_url),
        market_refresh_seconds=int(os.getenv("MARKET_REFRESH_SECONDS", str(defaults.market_refresh_seconds))),
        orderbook_poll_seconds=float(os.getenv("ORDERBOOK_POLL_SECONDS", str(defaults.orderbook_poll_seconds))),
        stale_feed_seconds=int(os.getenv("STALE_FEED_SECONDS", str(defaults.stale_feed_seconds))),
        orderbook_top_levels=int(os.getenv("ORDERBOOK_TOP_LEVELS", str(defaults.orderbook_top_levels))),
        btc_ws_url=os.getenv("BTC_WS_URL", defaults.btc_ws_url),
        btc_symbol=os.getenv("BTC_SYMBOL", defaults.btc_symbol),
        fee_rate=float(os.getenv("FEE_RATE", str(defaults.fee_rate))),
        slippage_buffer=float(os.getenv("SLIPPAGE_BUFFER", str(defaults.slippage_buffer))),
        latency_ms=int(os.getenv("LATENCY_MS", str(defaults.latency_ms))),
        min_trade_size=float(os.getenv("MIN_TRADE_SIZE", str(defaults.min_trade_size))),
        max_book_skew_ms=int(os.getenv("MAX_BOOK_SKEW_MS", str(defaults.max_book_skew_ms))),
        one_leg_fill_risk=float(os.getenv("ONE_LEG_FILL_RISK", str(defaults.one_leg_fill_risk))),
    )
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    return settings
