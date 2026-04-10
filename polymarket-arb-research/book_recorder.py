from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import timedelta

import aiohttp

from models import OrderBookLevel, OrderBookSnapshot
from storage import Storage
from utils import utc_now

LOG = logging.getLogger(__name__)


class PolymarketBookRecorder:
    def __init__(
        self,
        clob_base_url: str,
        storage: Storage,
        poll_seconds: float,
        top_levels: int,
        stale_feed_seconds: int,
    ):
        self.clob_base_url = clob_base_url.rstrip("/")
        self.storage = storage
        self.poll_seconds = poll_seconds
        self.top_levels = top_levels
        self.stale_feed_seconds = stale_feed_seconds
        self._last_snapshot_at = utc_now()
        self._buffer: deque[OrderBookSnapshot] = deque()

    async def run(self, stop_event: asyncio.Event) -> None:
        timeout = aiohttp.ClientTimeout(total=10)
        connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=60)
        backoff = 1.0

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            while not stop_event.is_set():
                pairs = await self.storage.read_token_pairs()
                token_ids = {p[1] for p in pairs} | {p[2] for p in pairs}
                if not token_ids:
                    await asyncio.sleep(self.poll_seconds)
                    continue

                failures = 0
                for token_id in token_ids:
                    snap = await self._fetch_book_snapshot(session, token_id)
                    if snap:
                        self._buffer.append(snap)
                        self._last_snapshot_at = utc_now()
                    else:
                        failures += 1

                if self._buffer and (len(self._buffer) >= 200 or failures > 0):
                    await self.storage.insert_orderbook_batch(self._flush_buffer())

                if failures == len(token_ids):
                    LOG.warning("All orderbook requests failed this cycle; retrying with backoff")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 10.0)
                else:
                    backoff = 1.0
                    await asyncio.sleep(self.poll_seconds)

                if utc_now() - self._last_snapshot_at > timedelta(seconds=self.stale_feed_seconds):
                    LOG.warning("Orderbook feed appears stale (>%ss)", self.stale_feed_seconds)

            if self._buffer:
                await self.storage.insert_orderbook_batch(self._flush_buffer())

    async def _fetch_book_snapshot(self, session: aiohttp.ClientSession, token_id: str) -> OrderBookSnapshot | None:
        url = f"{self.clob_base_url}/book"
        try:
            async with session.get(url, params={"token_id": token_id}) as resp:
                resp.raise_for_status()
                payload = await resp.json()
        except Exception as exc:
            LOG.warning("Book fetch failed token=%s err=%s", token_id, exc)
            return None

        bids_raw = payload.get("bids", [])[: self.top_levels]
        asks_raw = payload.get("asks", [])[: self.top_levels]
        try:
            bids = [OrderBookLevel(float(x["price"]), float(x["size"])) for x in bids_raw]
            asks = [OrderBookLevel(float(x["price"]), float(x["size"])) for x in asks_raw]
        except (TypeError, ValueError, KeyError):
            return None

        return OrderBookSnapshot(
            ts=utc_now(),
            token_id=token_id,
            best_bid_price=bids[0].price if bids else None,
            best_bid_size=bids[0].size if bids else None,
            best_ask_price=asks[0].price if asks else None,
            best_ask_size=asks[0].size if asks else None,
            bids=bids,
            asks=asks,
        )

    def _flush_buffer(self) -> list[OrderBookSnapshot]:
        rows = list(self._buffer)
        self._buffer.clear()
        return rows
