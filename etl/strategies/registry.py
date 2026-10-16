"""Strategy registry: build CompositeStrategy instances from strategies.yml."""

from __future__ import annotations

from etl.config import load_strategies  # type: ignore
from etl.strategies.base import CompositeStrategy, StrategyConfig


def build_strategies() -> dict:
    out = {}
    for sid, cfg in load_strategies().items():
        strategy_cfg = StrategyConfig(
            strategy_id=sid,
            factor_weights=dict(cfg.get("factor_weights", {})),
            filters=list(cfg.get("filters", [])),
            top_n=int(cfg.get("top_n", 20)),
            rebalance=str(cfg.get("rebalance", "monthly")),
            direction=str(cfg.get("direction", "BUY")),
        )
        out[sid] = CompositeStrategy(strategy_cfg)
    return out
