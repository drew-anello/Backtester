from __future__ import annotations
import argparse
from pathlib import Path

import yaml

from backtest.engine import BacktestEngine
from backtest.data_loader import CSVLoader, YFinanceLoader
from backtest.portfolio import Portfolio
from strategies.moving_average import MovingAverageCross
from metrics.report import summarize


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
        "strategy": {"short_window": 50, "long_window": 200},
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
    strat = MovingAverageCross(**cfg.get("strategy", {}))
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
