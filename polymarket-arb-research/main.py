from __future__ import annotations

import argparse
import asyncio
import logging
from contextlib import suppress

import aiohttp

from book_recorder import PolymarketBookRecorder
from btc_price_feed import BTCPriceRecorder
from config import load_settings
from market_discovery import MarketDiscovery
from opportunity_report import OpportunityReporter
from replay_backtest import ReplayBacktester
from storage import Storage
from utils import setup_logging, utc_now

LOG = logging.getLogger(__name__)


async def market_refresh_loop(
    storage: Storage,
    discovery: MarketDiscovery,
    refresh_seconds: int,
    stop_event: asyncio.Event,
) -> None:
    backoff = 1.0
    async with aiohttp.ClientSession() as session:
        while not stop_event.is_set():
            try:
                markets = await discovery.discover_btc_markets(session)
                await storage.upsert_markets(markets, utc_now())
                backoff = 1.0
                await asyncio.sleep(refresh_seconds)
            except Exception as exc:
                LOG.warning("Market discovery failed: %s", exc)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)


async def run_record(args: argparse.Namespace) -> None:
    settings = load_settings()
    settings.db_path = args.db_path or settings.db_path
    if args.market_refresh_interval:
        settings.market_refresh_seconds = args.market_refresh_interval

    storage = Storage(settings.db_path)
    await storage.init()

    discovery = MarketDiscovery(settings.polymarket_gamma_url)
    book_recorder = PolymarketBookRecorder(
        settings.polymarket_clob_url,
        storage,
        settings.orderbook_poll_seconds,
        settings.orderbook_top_levels,
        settings.stale_feed_seconds,
    )
    btc_recorder = BTCPriceRecorder(settings.btc_ws_url, settings.btc_symbol, storage)

    stop_event = asyncio.Event()
    tasks = [
        asyncio.create_task(market_refresh_loop(storage, discovery, settings.market_refresh_seconds, stop_event)),
        asyncio.create_task(book_recorder.run(stop_event)),
        asyncio.create_task(btc_recorder.run(stop_event)),
    ]

    LOG.info("Starting record run for %ss", args.duration)
    try:
        await asyncio.sleep(args.duration)
    finally:
        stop_event.set()
        for task in tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        await storage.close()


async def run_backtest(args: argparse.Namespace) -> None:
    settings = load_settings()
    settings.db_path = args.db_path or settings.db_path
    settings.fee_rate = args.fee_rate if args.fee_rate is not None else settings.fee_rate
    settings.slippage_buffer = args.slippage_buffer if args.slippage_buffer is not None else settings.slippage_buffer
    settings.latency_ms = args.latency_ms if args.latency_ms is not None else settings.latency_ms
    settings.min_trade_size = args.min_trade_size if args.min_trade_size is not None else settings.min_trade_size

    storage = Storage(settings.db_path)
    await storage.init()
    backtester = ReplayBacktester(storage, settings)
    summary = await backtester.run()
    await storage.close()

    print("=== Backtest Summary ===")
    print(f"Raw opportunities: {summary.raw_opportunity_count}")
    print(f"Executable opportunities: {summary.executable_opportunity_count}")
    print(f"Avg gross edge: {summary.average_gross_edge:.6f}")
    print(f"Avg net edge: {summary.average_net_edge:.6f}")
    print(f"Estimated PnL: {summary.estimated_pnl:.4f}")


async def run_report(args: argparse.Namespace) -> None:
    settings = load_settings()
    settings.db_path = args.db_path or settings.db_path
    storage = Storage(settings.db_path)
    await storage.init()
    reporter = OpportunityReporter(storage)
    rows = await reporter.load(executable_only=not args.include_non_executable)
    reporter.print_summary(rows, top_n=args.top_n)
    if args.csv_out:
        reporter.export_csv(rows, args.csv_out)
        print(f"CSV exported: {args.csv_out}")
    await storage.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Polymarket BTC complementary arb research")
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser("record", help="Record market/orderbook/BTC feeds")
    p_record.add_argument("--duration", type=int, default=3600)
    p_record.add_argument("--db-path", type=str)
    p_record.add_argument("--market-refresh-interval", type=int)

    p_backtest = sub.add_parser("backtest", help="Replay recorded data")
    p_backtest.add_argument("--db-path", type=str)
    p_backtest.add_argument("--slippage-buffer", type=float)
    p_backtest.add_argument("--latency-ms", type=int)
    p_backtest.add_argument("--fee-rate", type=float)
    p_backtest.add_argument("--min-trade-size", type=float)

    p_report = sub.add_parser("report", help="Print and export report")
    p_report.add_argument("--db-path", type=str)
    p_report.add_argument("--csv-out", type=str, default="data/processed/opportunities.csv")
    p_report.add_argument("--top-n", type=int, default=10)
    p_report.add_argument("--include-non-executable", action="store_true")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    setup_logging(load_settings().log_level)

    # TODO(live): this is where future live execution orchestrator could be wired in.
    if args.command == "record":
        asyncio.run(run_record(args))
    elif args.command == "backtest":
        asyncio.run(run_backtest(args))
    elif args.command == "report":
        asyncio.run(run_report(args))


if __name__ == "__main__":
    main()
