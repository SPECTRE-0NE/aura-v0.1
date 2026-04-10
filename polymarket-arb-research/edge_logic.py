from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EdgeResult:
    gross_edge: float
    fee_cost: float
    slippage_cost: float
    latency_cost: float
    fill_risk_cost: float
    net_edge: float


@dataclass(frozen=True, slots=True)
class ExecutionDecision:
    executable: bool
    reason: str


def calculate_edges(
    yes_ask: float,
    no_ask: float,
    fee_rate: float,
    slippage_buffer: float,
    latency_ms: int,
    one_leg_fill_risk: float,
) -> EdgeResult:
    gross = 1.0 - (yes_ask + no_ask)
    fee_cost = max(0.0, fee_rate)
    slippage_cost = max(0.0, slippage_buffer)
    latency_cost = max(0, latency_ms) / 1_000_000
    fill_risk_cost = max(0.0, one_leg_fill_risk) * max(0.0, gross)
    net = gross - fee_cost - slippage_cost - latency_cost - fill_risk_cost
    return EdgeResult(
        gross_edge=gross,
        fee_cost=fee_cost,
        slippage_cost=slippage_cost,
        latency_cost=latency_cost,
        fill_risk_cost=fill_risk_cost,
        net_edge=net,
    )


def decide_executable(
    edge: EdgeResult,
    yes_size: float | None,
    no_size: float | None,
    min_trade_size: float,
    survives_latency: bool,
) -> ExecutionDecision:
    if yes_size is None or no_size is None or yes_size <= 0 or no_size <= 0:
        return ExecutionDecision(False, "missing_or_zero_size")

    if min(yes_size, no_size) < min_trade_size:
        return ExecutionDecision(False, "below_min_size")

    if edge.gross_edge <= 0:
        return ExecutionDecision(False, "no_raw_gap")

    if not survives_latency:
        return ExecutionDecision(False, "vanished_before_execution")

    if edge.net_edge <= 0:
        return ExecutionDecision(False, "non_positive_net_edge")

    return ExecutionDecision(True, "executable")
