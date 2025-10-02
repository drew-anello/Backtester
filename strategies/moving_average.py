from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class MovingAverageCross:
    short_window: int = 20
    long_window: int = 50
    prices: deque[float] = field(default_factory=lambda: deque(maxlen=0))

    def __post_init__(self):
        if self.long_window <= 0 or self.short_window <= 0:
            raise ValueError("Windows must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be < long_window")
        # Set maxlen to the longest window to keep minimal state
        self.prices = deque(maxlen=self.long_window)

    def on_bar(self, bar: dict) -> dict:
        close = float(bar.get("close"))
        self.prices.append(close)
        if len(self.prices) < self.long_window:
            return {"target_weight": 0.0}

        # Compute SMAs efficiently
        long_sma = sum(self.prices) / self.long_window
        # short SMA is last short_window prices
        short_sum = 0.0
        for i, p in enumerate(reversed(self.prices)):
            if i >= self.short_window:
                break
            short_sum += p
        short_sma = short_sum / self.short_window

        target = 1.0 if short_sma > long_sma else 0.0
        return {"target_weight": target}
