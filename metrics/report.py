from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd


def _compute_drawdown(equity: pd.Series) -> tuple[float, float]:
    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    max_dd = dd.min()
    end_idx = dd.idxmin()
    # Find start of the drawdown
    start_idx = (equity.loc[:end_idx]).idxmax()
    return float(max_dd), float((end_idx - start_idx).days) if hasattr(end_idx, 'to_pydatetime') else 0.0


def summarize(history: Iterable[dict], results_dir: str = "results") -> dict:
    """Compute basic stats and save equity curve to CSV.

    history: iterable of dicts with keys: date, value
    """
    if not history:
        return {}

    df = pd.DataFrame(history)
    # Coerce date to datetime index
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])  # type: ignore[arg-type]
        df = df.set_index("date").sort_index()

    equity = df["value"].astype(float)
    rets = equity.pct_change().fillna(0.0)

    periods_per_year = 252  # assume daily
    tot_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    cagr = float((1.0 + tot_return) ** (1 / years) - 1.0) if years > 0 else 0.0

    vol = float(rets.std() * (periods_per_year ** 0.5))
    sharpe = float((rets.mean() * periods_per_year) / vol) if vol > 0 else 0.0

    max_dd, dd_days = _compute_drawdown(equity)

    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    out_csv = results_path / "equity.csv"
    df.to_csv(out_csv)

    # Generate equity curve plot
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df.index, equity, label="Equity")
    ax.set_title("Backtest Equity Curve")
    ax.set_ylabel("Portfolio Value")
    ax.set_xlabel("Date")
    ax.legend()
    fig.autofmt_xdate()
    out_png = results_path / "equity.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "start_value": float(equity.iloc[0]),
        "end_value": float(equity.iloc[-1]),
        "total_return": tot_return,
        "CAGR": cagr,
        "volatility": vol,
        "Sharpe": sharpe,
        "max_drawdown": float(max_dd),
        "max_drawdown_days": dd_days,
        "equity_path": str(out_csv),
        "equity_plot": str(out_png),
    }
