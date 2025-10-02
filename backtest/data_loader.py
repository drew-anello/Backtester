from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

import polars as pl


@dataclass
class CSVLoader:
    """Simple CSV loader returning an iterator over rows.

    Expects at least columns: date, close (and optionally symbol, open, high, low, volume).
    """

    path: str
    date_col: str = "date"

    def load(self, start: Optional[str] = None, end: Optional[str] = None) -> Iterator[dict]:
        df = pl.read_csv(self.path, try_parse_dates=True)
        if self.date_col not in df.columns:
            raise ValueError(f"CSV missing required '{self.date_col}' column")
        # Ensure date column is of dtype Date/Datetime
        if df[self.date_col].dtype not in (pl.Date, pl.Datetime):
            df = df.with_columns(pl.col(self.date_col).strptime(pl.Datetime, strict=False))

        if start is not None:
            df = df.filter(pl.col(self.date_col) >= pl.lit(start))
        if end is not None:
            df = df.filter(pl.col(self.date_col) <= pl.lit(end))

        # Sort by time to ensure correct order
        df = df.sort(self.date_col)

        # Yield as dict per bar for the engine loop
        for row in df.iter_rows(named=True):
            yield row
