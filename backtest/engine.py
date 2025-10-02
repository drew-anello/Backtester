from dataclasses import dataclass
from typing import Iterable
from .portfolio import Portfolio
from .reporter import Reporter
from .strategy import Strategy
from .data_loader import DataLoader

@dataclass
class BacktestEngine:
    data_loader: "DataLoader"
    strategy: "Strategy"
    portfolio: "Portfolio"
    reporters: Iterable["Reporter"]

    def run(self, start: str, end: str) -> None:
        data = self.data_loader.load(start=start, end=end)
        for bar in data:
            signal = self.strategy.on_bar(bar)
            orders = self.portfolio.generate_orders(signal, bar)
            fills = self.portfolio.execute_orders(orders, bar)
            self.portfolio.update(fills, bar)
        for reporter in self.reporters:
            reporter.generate(self.portfolio.history)
