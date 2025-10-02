from __future__ import annotations

import argparse
from pathlib import Path
import random

import polars as pl
import yaml

# Local imports
from backtest.engine import BacktestEngine
from backtest.data_loader import CSVLoader
from backtest.portfolio import Portfolio
from strategies.moving_average import MovingAverageCross
from metrics.report import summarize


def generate_sine_data(path: Path, n: int = 600) -> None:
    import math
    import datetime as dt

    start = dt.date(2015, 1, 1)
    rows = []
    price = 100.0
    for i in range(n):
        d = start + dt.timedelta(days=i)
        if d.weekday() >= 5:  # skip weekends to simulate trading days
            continue
        price *= 1.0 + 0.001 * math.sin(i / 20.0) + random.uniform(-0.003, 0.003)
        rows.append({"date": d.isoformat(), "close": round(price, 4)})
    pl.DataFrame(rows).write_csv(str(path))


def load_config(cfg_path: Path | None) -> dict:
    if cfg_path and cfg_path.exists():
        with open(cfg_path, "r") as f:
            return yaml.safe_load(f) or {}
    # defaults
    return {
        "data_path": "data/demo.csv",
        "initial_cash": 100_000,
        "start": "2018-01-01",
        "end": "2024-12-31",
        "strategy": {"short_window": 20, "long_window": 50},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/demo.yaml")
    args = parser.parse_args(argv)

    cfg = load_config(Path(args.config))

    data_path = Path(cfg.get("data_path", "data/demo.csv"))
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if not data_path.exists():
        print(f"Generating synthetic data at {data_path}...")
        generate_sine_data(data_path)

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
