from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

import pandas as pd
import polars as pl
import yfinance as yf


CANON_COLS = ["open", "high", "low", "close", "volume"]


def _to_canonical(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    renamed = df.rename(columns=str.lower)
    missing = [c for c in CANON_COLS if c not in renamed.columns]
    if missing:
        raise ValueError(f"Downloaded data for {symbol} missing columns: {missing}")
    out = renamed[CANON_COLS].copy()
    out["symbol"] = symbol.upper()
    out.index.name = "date"
    out = out.reset_index()
    out["date"] = pd.to_datetime(out["date"])
    return out


def download_and_cache(
    symbols: list[str],
    start: str,
    end: str,
    root: str = "data/equities",
) -> pd.DataFrame:
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []

    for sym in symbols:
        raw = yf.download(sym, start=start, end=end, auto_adjust=True, progress=False)
        if raw.empty:
            continue
        canon = _to_canonical(raw, sym)
        canon["year"] = canon["date"].dt.year
        for year, group in canon.groupby("year"):
            year_path = root_path / f"symbol={sym.upper()}" / f"year={int(year)}"
            year_path.mkdir(parents=True, exist_ok=True)
            group.drop(columns="year").to_parquet(year_path / "part-000.parquet", index=False)
        frames.append(canon.drop(columns="year"))

    if not frames:
        raise RuntimeError("No data downloaded for requested symbols/timeframe.")

    all_df = pd.concat(frames, ignore_index=True)
    all_df["date"] = pd.to_datetime(all_df["date"])
    all_df = all_df.set_index(["date", "symbol"]).sort_index()
    return all_df


def load_prices(
    root: str = "data/equities",
    symbols: Optional[list[str]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"No cached data under {root_path}")

    # Ensure there are parquet files before scanning
    if not any(root_path.glob("**/*.parquet")):
        raise RuntimeError(f"No parquet files found in cache {root_path}")

    pattern = str(root_path / "**" / "*.parquet")
    lf = pl.scan_parquet(pattern)

    if symbols:
        lf = lf.filter(pl.col("symbol").is_in([s.upper() for s in symbols]))

    lf = lf.select(
        pl.col("date").cast(pl.Datetime).alias("date"),
        pl.col("symbol").str.to_uppercase().alias("symbol"),
        *[pl.col(c).alias(c) for c in CANON_COLS],
    )

    df = lf.collect().to_pandas()
    if df.empty:
        raise RuntimeError("Cached dataset is empty after filtering")

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index(["date", "symbol"]).sort_index()

    if start or end:
        start_ts = pd.to_datetime(start) if start else None
        end_ts = pd.to_datetime(end) if end else None
        idx = pd.IndexSlice
        df = df.loc[idx[start_ts:end_ts, :]] if start_ts or end_ts else df

    return df


@dataclass
class CSVLoader:
    """Simple CSV loader returning an iterator over rows."""

    path: str
    date_col: str = "date"

    def load(self, start: Optional[str] = None, end: Optional[str] = None) -> Iterator[dict]:
        df = pl.read_csv(self.path, try_parse_dates=True)
        if self.date_col not in df.columns:
            raise ValueError(f"CSV missing required '{self.date_col}' column")
        if df[self.date_col].dtype not in (pl.Date, pl.Datetime):
            df = df.with_columns(pl.col(self.date_col).strptime(pl.Datetime, strict=False))

        if start is not None:
            df = df.filter(pl.col(self.date_col) >= pl.lit(start))
        if end is not None:
            df = df.filter(pl.col(self.date_col) <= pl.lit(end))

        df = df.sort(self.date_col)

        for row in df.iter_rows(named=True):
            yield row


@dataclass
class YFinanceLoader:
    symbols: list[str]
    root: str = "data/equities"

    def load(self, start: Optional[str] = None, end: Optional[str] = None) -> Iterator[dict]:
        if start is None or end is None:
            raise ValueError("YFinanceLoader requires both start and end dates")

        df = download_and_cache(self.symbols, start=start, end=end, root=self.root)
        df = df.loc[(slice(pd.to_datetime(start), pd.to_datetime(end)), slice(None)), :]

        for (date, symbol), row in df.iterrows():
            yield {
                "date": date.to_pydatetime(),
                "symbol": symbol,
                **{col: float(row[col]) for col in CANON_COLS},
            }
