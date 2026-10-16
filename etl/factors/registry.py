"""Factor registry: factor_id -> compute function, plus category metadata."""

from __future__ import annotations

from etl.factors import growth, liquidity, momentum, quality, valuation, volatility
from etl.factors.base import FactorFn

CATEGORY_BY_MODULE = {
    valuation: "valuation",
    quality: "quality",
    growth: "growth",
    momentum: "momentum",
    volatility: "volatility",
    liquidity: "liquidity",
}

ALL_FACTORS: dict[str, FactorFn] = {}
FACTOR_CATEGORY: dict[str, str] = {}
for _mod, _cat in CATEGORY_BY_MODULE.items():
    for _fid, _fn in _mod.FACTORS.items():
        ALL_FACTORS[_fid] = _fn
        FACTOR_CATEGORY[_fid] = _cat
