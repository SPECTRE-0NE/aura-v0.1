from __future__ import annotations

import bisect
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from config import Settings
from edge_logic import calculate_edges, decide_executable
from models import BacktestSummary, Opportunity
from storage import Storage
from utils import parse_maybe_ts, safe_mean

LOG = logging.getLogger(__name__)


@dataclass(slots=True)
class BookPoint:
    ts: datetime
    ask: float | None
    ask_size: float | None


class ReplayBacktester:
    def __init__(self, storage: Storage, settings: Settings):
        self.storage = storage
        self.settings = settings
        self._btc_times: list[datetime] = []
        self._btc_prices: list[float] = []

    async def run(self) -> BacktestSummary:
        pairs = await self.storage.read_token_pairs()
        self._load_btc_ticks(await self.storage.read_btc_ticks())

        opportunities: list[Opportunity] = []
        for market_id, yes_token, no_token in pairs:
            yes_books = await self.storage.read_orderbooks_for_token(yes_token)
            no_books = await self.storage.read_orderbooks_for_token(no_token)
            if not yes_books or not no_books:
                continue
            opportunities.extend(
                self._evaluate_market_pair(market_id, yes_token, no_token, yes_books, no_books)
            )

        await self.storage.insert_opportunities(opportunities)

        raw = len(opportunities)
        executable = sum(1 for o in opportunities if o.executable)
        avg_gross = safe_mean([o.gross_edge for o in opportunities])
        avg_net = safe_mean([o.net_edge for o in opportunities])
        est_pnl = sum(max(0.0, o.net_edge) * min(o.size_yes, o.size_no) for o in opportunities if o.executable)

        breakdown = defaultdict(lambda: {"raw": 0, "exec": 0, "avg_net": 0.0})
        for o in opportunities:
            b = breakdown[o.market_id]
            b["raw"] += 1
            b["exec"] += int(o.executable)
        for market_id in list(breakdown):
            market_nets = [o.net_edge for o in opportunities if o.market_id == market_id]
            breakdown[market_id]["avg_net"] = safe_mean(market_nets)

        return BacktestSummary(
            raw_opportunity_count=raw,
            executable_opportunity_count=executable,
            average_gross_edge=avg_gross,
            average_net_edge=avg_net,
            estimated_pnl=est_pnl,
            market_breakdown=dict(breakdown),
        )

    def _evaluate_market_pair(
        self,
        market_id: str,
        yes_token: str,
        no_token: str,
        yes_rows: list[tuple],
        no_rows: list[tuple],
    ) -> list[Opportunity]:
        yes = [BookPoint(_to_dt(r[0]), r[2], r[3]) for r in yes_rows]
        no = [BookPoint(_to_dt(r[0]), r[2], r[3]) for r in no_rows]

        i = j = 0
        out: list[Opportunity] = []
        while i < len(yes) and j < len(no):
            y, n = yes[i], no[j]
            delta_ms = abs((y.ts - n.ts).total_seconds() * 1000)
            if delta_ms > self.settings.max_book_skew_ms:
                if y.ts < n.ts:
                    i += 1
                else:
                    j += 1
                continue

            if y.ask is not None and n.ask is not None:
                edge = calculate_edges(
                    yes_ask=y.ask,
                    no_ask=n.ask,
                    fee_rate=self.settings.fee_rate,
                    slippage_buffer=self.settings.slippage_buffer,
                    latency_ms=self.settings.latency_ms,
                    one_leg_fill_risk=self.settings.one_leg_fill_risk,
                )
                survives = self._survives_latency(yes, no, i, j)
                decision = decide_executable(
                    edge=edge,
                    yes_size=y.ask_size,
                    no_size=n.ask_size,
                    min_trade_size=self.settings.min_trade_size,
                    survives_latency=survives,
                )

                if edge.gross_edge > 0:
                    event_ts = min(y.ts, n.ts)
                    out.append(
                        Opportunity(
                            ts_start=event_ts,
                            ts_end=max(y.ts, n.ts) + timedelta(milliseconds=self.settings.latency_ms),
                            market_id=market_id,
                            yes_token_id=yes_token,
                            no_token_id=no_token,
                            yes_ask=y.ask,
                            no_ask=n.ask,
                            size_yes=y.ask_size or 0.0,
                            size_no=n.ask_size or 0.0,
                            gross_edge=edge.gross_edge,
                            fee_cost=edge.fee_cost,
                            slippage_cost=edge.slippage_cost,
                            latency_cost=edge.latency_cost,
                            net_edge=edge.net_edge,
                            executable=decision.executable,
                            btc_price=self._nearest_btc_price(event_ts),
                            notes=decision.reason,
                        )
                    )

            if y.ts <= n.ts:
                i += 1
            else:
                j += 1

        LOG.info("Backtest market=%s opportunities=%s", market_id, len(out))
        return out

    def _survives_latency(self, yes: list[BookPoint], no: list[BookPoint], yi: int, ni: int) -> bool:
        latency = timedelta(milliseconds=self.settings.latency_ms)
        target_y = yes[yi].ts + latency
        target_n = no[ni].ts + latency

        y_future = next((p for p in yes[yi:] if p.ts >= target_y and p.ask is not None), None)
        n_future = next((p for p in no[ni:] if p.ts >= target_n and p.ask is not None), None)
        if not y_future or not n_future:
            return False
        return (y_future.ask + n_future.ask) < 1.0

    def _load_btc_ticks(self, rows: list[tuple[str, float]]) -> None:
        self._btc_times = []
        self._btc_prices = []
        for ts_iso, price in rows:
            ts = parse_maybe_ts(ts_iso)
            if ts is None:
                continue
            self._btc_times.append(ts)
            self._btc_prices.append(float(price))

    def _nearest_btc_price(self, ts: datetime) -> float | None:
        if not self._btc_times:
            return None
        idx = bisect.bisect_left(self._btc_times, ts)
        if idx <= 0:
            return self._btc_prices[0]
        if idx >= len(self._btc_times):
            return self._btc_prices[-1]
        prev_dt, next_dt = self._btc_times[idx - 1], self._btc_times[idx]
        if abs((ts - prev_dt).total_seconds()) <= abs((next_dt - ts).total_seconds()):
            return self._btc_prices[idx - 1]
        return self._btc_prices[idx]


def _to_dt(ts_iso: str) -> datetime:
    parsed = parse_maybe_ts(ts_iso)
    return parsed if parsed else datetime.fromtimestamp(0, tz=timezone.utc)
