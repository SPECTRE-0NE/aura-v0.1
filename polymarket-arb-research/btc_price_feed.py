from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from datetime import datetime

import websockets

from models import BTCTick
from storage import Storage
from utils import from_unix_ms, utc_now

LOG = logging.getLogger(__name__)


class BTCPriceRecorder:
    def __init__(self, ws_url: str, symbol: str, storage: Storage):
        self.ws_url = ws_url
        self.symbol = symbol
        self.storage = storage
        self._latest_price: float | None = None
        self._buffer: deque[BTCTick] = deque()

    @property
    def latest_price(self) -> float | None:
        return self._latest_price

    async def run(self, stop_event: asyncio.Event) -> None:
        backoff = 1.0
        while not stop_event.is_set():
            try:
                await self._run_once(stop_event)
                backoff = 1.0
            except Exception as exc:
                LOG.warning("BTC feed connection dropped: %s", exc)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 20.0)

        if self._buffer:
            await self.storage.insert_btc_ticks_batch(self._flush_buffer())

    async def _run_once(self, stop_event: asyncio.Event) -> None:
        async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=20, open_timeout=15) as ws:
            LOG.info("Connected BTC feed: %s", self.ws_url)
            while not stop_event.is_set():
                msg = await asyncio.wait_for(ws.recv(), timeout=30)
                payload = json.loads(msg)
                price = self._extract_price(payload)
                if price is None:
                    continue

                ts = self._extract_ts(payload)
                self._latest_price = price
                self._buffer.append(BTCTick(ts=ts, symbol=self.symbol, price=price))
                if len(self._buffer) >= 500:
                    await self.storage.insert_btc_ticks_batch(self._flush_buffer())

    @staticmethod
    def _extract_price(payload: dict) -> float | None:
        for key in ("p", "price", "last"):
            if key in payload:
                try:
                    return float(payload[key])
                except (TypeError, ValueError):
                    return None
        return None

    @staticmethod
    def _extract_ts(payload: dict) -> datetime:
        # Binance trade time is usually ms in key `T` or event time `E`.
        raw = payload.get("T", payload.get("E"))
        if isinstance(raw, (int, float)):
            return from_unix_ms(raw)
        return utc_now()

    def _flush_buffer(self) -> list[BTCTick]:
        rows = list(self._buffer)
        self._buffer.clear()
        return rows
