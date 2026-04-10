from __future__ import annotations

import logging
import re
import aiohttp

from models import Market
from utils import parse_maybe_ts, utc_now

LOG = logging.getLogger(__name__)


class MarketDiscovery:
    def __init__(self, gamma_base_url: str):
        self.gamma_base_url = gamma_base_url.rstrip("/")

    async def discover_btc_markets(self, session: aiohttp.ClientSession, limit: int = 200) -> list[Market]:
        # Gamma API shape can evolve; we keep parsing defensive and skip malformed rows.
        url = f"{self.gamma_base_url}/markets"
        params = {"active": "true", "closed": "false", "limit": str(limit)}
        async with session.get(url, params=params, timeout=20) as resp:
            resp.raise_for_status()
            payload = await resp.json()

        rows = payload if isinstance(payload, list) else payload.get("data", [])
        markets: list[Market] = []
        for row in rows:
            question = str(row.get("question", ""))
            slug = str(row.get("slug", ""))
            if "btc" not in question.lower() and "bitcoin" not in question.lower() and "btc" not in slug.lower():
                continue

            tokens = row.get("tokens") or []
            yes_token = self._pick_token(tokens, "yes")
            no_token = self._pick_token(tokens, "no")
            if not yes_token or not no_token:
                continue

            strike = self._infer_strike(question)
            expiry = parse_maybe_ts(row.get("endDate") or row.get("end_date_iso"))
            if expiry and (expiry - utc_now()).days > 14:
                # short-duration preference: skip markets far from expiry.
                continue

            markets.append(
                Market(
                    market_id=str(row.get("id") or row.get("conditionId") or slug),
                    question=question,
                    slug=slug,
                    expiry_ts=expiry,
                    yes_token_id=str(yes_token.get("token_id") or yes_token.get("id")),
                    no_token_id=str(no_token.get("token_id") or no_token.get("id")),
                    strike=strike,
                    is_active=bool(row.get("active", True)),
                )
            )

        LOG.info("Discovered %s active BTC markets", len(markets))
        return markets

    @staticmethod
    def _pick_token(tokens: list[dict], outcome: str) -> dict | None:
        for token in tokens:
            if str(token.get("outcome", "")).strip().lower() == outcome:
                return token
        return None

    @staticmethod
    def _infer_strike(question: str) -> float | None:
        # Extract thresholds like "$95k" / "95,000" from question text.
        m = re.search(r"\$?([0-9]{2,3}(?:,[0-9]{3})+|[0-9]{4,6})(?:k|K)?", question)
        if not m:
            return None
        value = float(m.group(1).replace(",", ""))
        if question[m.start():m.end()].lower().endswith("k"):
            value *= 1_000
        return value
