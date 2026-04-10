from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime

import aiosqlite

from models import BTCTick, Market, Opportunity, OrderBookSnapshot
from utils import to_iso


class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self._conn is not None:
            return
        self._conn = await aiosqlite.connect(self.db_path)
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._conn.execute("PRAGMA temp_store=MEMORY;")

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def init(self) -> None:
        await self.connect()
        assert self._conn is not None
        await self._conn.executescript(
            """
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
            """
        )
        await self._conn.commit()

    async def upsert_markets(self, markets: list[Market], updated_at: datetime) -> None:
        if not markets:
            return
        assert self._conn is not None
        await self._conn.executemany(
            """
            INSERT INTO markets(market_id, question, slug, expiry_ts, strike, is_active, updated_at)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(market_id) DO UPDATE SET
              question=excluded.question,
              slug=excluded.slug,
              expiry_ts=excluded.expiry_ts,
              strike=excluded.strike,
              is_active=excluded.is_active,
              updated_at=excluded.updated_at
            """,
            [
                (m.market_id, m.question, m.slug, to_iso(m.expiry_ts), m.strike, int(m.is_active), to_iso(updated_at))
                for m in markets
            ],
        )
        await self._conn.executemany(
            """
            INSERT OR REPLACE INTO token_pairs(market_id, yes_token_id, no_token_id)
            VALUES(?, ?, ?)
            """,
            [(m.market_id, m.yes_token_id, m.no_token_id) for m in markets],
        )
        await self._conn.commit()

    async def insert_orderbook_batch(self, rows: Iterable[OrderBookSnapshot]) -> None:
        rows_list = list(rows)
        if not rows_list:
            return
        assert self._conn is not None
        await self._conn.executemany(
            """
            INSERT INTO orderbook_snapshots(
                ts, token_id, best_bid_price, best_bid_size, best_ask_price, best_ask_size, bids_json, asks_json, source
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    to_iso(r.ts),
                    r.token_id,
                    r.best_bid_price,
                    r.best_bid_size,
                    r.best_ask_price,
                    r.best_ask_size,
                    json.dumps([l.__dict__ for l in r.bids]),
                    json.dumps([l.__dict__ for l in r.asks]),
                    r.source,
                )
                for r in rows_list
            ],
        )
        await self._conn.commit()

    async def insert_btc_ticks_batch(self, rows: Iterable[BTCTick]) -> None:
        rows_list = list(rows)
        if not rows_list:
            return
        assert self._conn is not None
        await self._conn.executemany(
            "INSERT INTO btc_ticks(ts, symbol, price, source) VALUES(?, ?, ?, ?)",
            [(to_iso(r.ts), r.symbol, r.price, r.source) for r in rows_list],
        )
        await self._conn.commit()

    async def insert_opportunities(self, rows: Iterable[Opportunity]) -> None:
        rows_list = list(rows)
        if not rows_list:
            return
        assert self._conn is not None
        await self._conn.executemany(
            """
            INSERT INTO opportunities(
                ts_start, ts_end, market_id, yes_token_id, no_token_id,
                gross_edge, net_edge, executable, fee_cost, slippage_cost, latency_cost,
                btc_price, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    to_iso(r.ts_start),
                    to_iso(r.ts_end),
                    r.market_id,
                    r.yes_token_id,
                    r.no_token_id,
                    r.gross_edge,
                    r.net_edge,
                    int(r.executable),
                    r.fee_cost,
                    r.slippage_cost,
                    r.latency_cost,
                    r.btc_price,
                    r.notes,
                )
                for r in rows_list
            ],
        )
        await self._conn.commit()

    async def read_token_pairs(self) -> list[tuple[str, str, str]]:
        assert self._conn is not None
        cur = await self._conn.execute("SELECT market_id, yes_token_id, no_token_id FROM token_pairs")
        return await cur.fetchall()

    async def read_orderbooks_for_token(self, token_id: str) -> list[tuple]:
        assert self._conn is not None
        cur = await self._conn.execute(
            """
            SELECT ts, token_id, best_ask_price, best_ask_size, best_bid_price, best_bid_size
            FROM orderbook_snapshots
            WHERE token_id = ?
            ORDER BY ts ASC
            """,
            (token_id,),
        )
        return await cur.fetchall()

    async def read_nearest_btc_price(self, ts_iso: str) -> float | None:
        assert self._conn is not None
        cur = await self._conn.execute(
            """
            SELECT price FROM btc_ticks
            ORDER BY ABS(strftime('%s', ts) - strftime('%s', ?)) ASC
            LIMIT 1
            """,
            (ts_iso,),
        )
        row = await cur.fetchone()
        return row[0] if row else None


    async def read_btc_ticks(self) -> list[tuple[str, float]]:
        assert self._conn is not None
        cur = await self._conn.execute("SELECT ts, price FROM btc_ticks ORDER BY ts ASC")
        return await cur.fetchall()

    async def fetch_opportunities(self, executable_only: bool = True) -> list[tuple]:
        assert self._conn is not None
        where_clause = "WHERE executable = 1" if executable_only else ""
        cur = await self._conn.execute(
            f"""
            SELECT ts_start, ts_end, market_id, gross_edge, net_edge, executable, btc_price, notes
            FROM opportunities
            {where_clause}
            ORDER BY net_edge DESC
            """
        )
        return await cur.fetchall()
