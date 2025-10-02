from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class MeanReversionStrategy:
    """Simple long-only mean reversion using z-score thresholds."""

    lookback: int = 20
    entry_z: float = 1.5
    exit_z: float = 0.5
    prices: deque[float] = field(default_factory=deque, init=False)
    _long: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.lookback <= 1:
            raise ValueError("lookback must be greater than 1")
        if self.entry_z <= 0 or self.exit_z <= 0:
            raise ValueError("entry_z and exit_z must be positive")
        if self.entry_z <= self.exit_z:
            raise ValueError("entry_z must be greater than exit_z")
        self.prices = deque(maxlen=self.lookback)

    def on_bar(self, bar: dict) -> dict:
        close = float(bar.get("close"))
        self.prices.append(close)
        if len(self.prices) < self.lookback:
            return {"target_weight": 0.0}

        mean = sum(self.prices) / len(self.prices)
        variance = sum((price - mean) ** 2 for price in self.prices) / len(self.prices)
        std = variance ** 0.5
        if std == 0.0:
            return {"target_weight": 0.0}

        z_score = (close - mean) / std
        if not self._long and z_score <= -self.entry_z:
            self._long = True
        elif self._long and z_score >= -self.exit_z:
            self._long = False
        return {"target_weight": 1.0 if self._long else 0.0}
