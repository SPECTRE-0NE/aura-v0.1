from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from storage import Storage
from utils import percentile


class OpportunityReporter:
    def __init__(self, storage: Storage):
        self.storage = storage

    async def load(self, executable_only: bool = True) -> list[tuple]:
        return await self.storage.fetch_opportunities(executable_only=executable_only)

    @staticmethod
    def print_summary(rows: list[tuple], top_n: int = 10) -> None:
        if not rows:
            print("No opportunities found under current filters.")
            return

        net_edges = [float(r[4]) for r in rows]
        conservative_edges = [e for e in net_edges if e > 0]
        print("=== Opportunity Summary (Conservative) ===")
        print("Showing rows already filtered for executability unless --include-non-executable is used.")
        print(f"Rows considered: {len(rows)}")
        print(f"Positive net-edge rows: {len(conservative_edges)}")
        print(f"Median net edge: {percentile(net_edges, 0.5):.6f}")
        print(f"P10 net edge: {percentile(net_edges, 0.1):.6f}")
        print(f"P90 net edge: {percentile(net_edges, 0.9):.6f}")

        print("\nTop opportunities by net edge:")
        for r in rows[:top_n]:
            print(f"  market={r[2]} net_edge={float(r[4]):.6f} gross={float(r[3]):.6f} ts={r[0]} note={r[7]}")

        by_market = defaultdict(list)
        by_hour = defaultdict(list)
        for r in rows:
            edge = float(r[4])
            by_market[r[2]].append(edge)
            hour = datetime.fromisoformat(r[0].replace("Z", "+00:00")).astimezone(timezone.utc).hour
            by_hour[hour].append(edge)

        print("\nBy market (median / P10 / count):")
        for market_id, vals in by_market.items():
            print(
                f"  {market_id}: median={percentile(vals, 0.5):.6f} p10={percentile(vals, 0.1):.6f} count={len(vals)}"
            )

        print("\nBy UTC hour (median / P10 / count):")
        for hour in sorted(by_hour):
            vals = by_hour[hour]
            print(
                f"  {hour:02d}:00 median={percentile(vals, 0.5):.6f} p10={percentile(vals, 0.1):.6f} count={len(vals)}"
            )

    @staticmethod
    def export_csv(rows: list[tuple], out_path: str) -> None:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "ts_start",
                    "ts_end",
                    "market_id",
                    "gross_edge",
                    "net_edge",
                    "executable",
                    "btc_price",
                    "notes",
                ]
            )
            writer.writerows(rows)
