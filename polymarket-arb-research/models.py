from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Market:
    market_id: str
    question: str
    slug: str
    expiry_ts: datetime | None
    yes_token_id: str
    no_token_id: str
    strike: float | None = None
    is_active: bool = True


@dataclass(slots=True)
class OrderBookLevel:
    price: float
    size: float


@dataclass(slots=True)
class OrderBookSnapshot:
    ts: datetime
    token_id: str
    best_bid_price: float | None
    best_bid_size: float | None
    best_ask_price: float | None
    best_ask_size: float | None
    bids: list[OrderBookLevel] = field(default_factory=list)
    asks: list[OrderBookLevel] = field(default_factory=list)
    source: str = "polymarket_public"


@dataclass(slots=True)
class BTCTick:
    ts: datetime
    symbol: str
    price: float
    source: str = "binance_ws"


@dataclass(slots=True)
class Opportunity:
    ts_start: datetime
    ts_end: datetime
    market_id: str
    yes_token_id: str
    no_token_id: str
    yes_ask: float
    no_ask: float
    size_yes: float
    size_no: float
    gross_edge: float
    fee_cost: float
    slippage_cost: float
    latency_cost: float
    net_edge: float
    executable: bool
    btc_price: float | None
    notes: str = ""


@dataclass(slots=True)
class BacktestSummary:
    raw_opportunity_count: int
    executable_opportunity_count: int
    average_gross_edge: float
    average_net_edge: float
    estimated_pnl: float
    market_breakdown: dict[str, dict[str, Any]]


@dataclass(slots=True)
class RunMetadata:
    run_type: str
    started_at: datetime
    finished_at: datetime | None
    config_json: str
    notes: str = ""
