from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any

import yaml

from backtest.engine import BacktestEngine
from backtest.data_loader import CSVLoader, YFinanceLoader
from backtest.portfolio import Portfolio
from metrics.report import summarize
from strategies.mean_reversion import MeanReversionStrategy
from strategies.moving_average import MovingAverageCross


STRATEGY_REGISTRY: dict[str, tuple[type[Any], dict[str, Any]]] = {
    "moving_average": (
        MovingAverageCross,
        {"short_window": 50, "long_window": 200},
    ),
    "mean_reversion": (
        MeanReversionStrategy,
        {"lookback": 20, "entry_z": 1.5, "exit_z": 0.5},
    ),
}


def build_strategy(config: dict[str, Any]) -> Any:
    cfg_copy = dict(config or {})
    strategy_type = str(cfg_copy.pop("type", "moving_average"))
    if strategy_type not in STRATEGY_REGISTRY:
        supported = ", ".join(sorted(STRATEGY_REGISTRY))
        raise ValueError(
            f"Unknown strategy type '{strategy_type}'. Supported types: {supported}"
        )
    cls, defaults = STRATEGY_REGISTRY[strategy_type]
    params = {**defaults, **cfg_copy}
    return cls(**params)


def load_config(cfg_path: Path | None) -> dict:
    if cfg_path and cfg_path.exists():
        with open(cfg_path, "r") as f:
            return yaml.safe_load(f) or {}
    # defaults
    return {
        "symbols": ["AAPL"],
        "data_root": "data/equities",
        "initial_cash": 100_000,
        "start": "2018-01-01",
        "end": "2024-12-31",
        "strategy": {"type": "moving_average"},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/demo.yaml")
    args = parser.parse_args(argv)

    cfg = load_config(Path(args.config))

    symbols = cfg.get("symbols")
    data_root = cfg.get("data_root", "data/equities")

    if symbols:
        loader = YFinanceLoader(symbols=list(symbols), root=str(data_root))
    else:
        data_path = Path(cfg.get("data_path", "data/demo.csv"))
        data_path.parent.mkdir(parents=True, exist_ok=True)
        loader = CSVLoader(str(data_path))
    strat = build_strategy(cfg.get("strategy", {}))
    portfolio = Portfolio(cash=float(cfg.get("initial_cash", 100_000)))

    engine = BacktestEngine(
        data_loader=loader,
        strategy=strat,
        portfolio=portfolio,
        reporters=[],
    )

    engine.run(start=str(cfg.get("start")), end=str(cfg.get("end")))
    stats = summarize(portfolio.history)
    print("\n=== Demo Summary ===")
    for k, v in stats.items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
