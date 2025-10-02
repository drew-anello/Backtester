from dataclasses import dataclass
from typing import Iterable, Protocol, runtime_checkable


@runtime_checkable
class DataLoader(Protocol):
    def load(self, start: str, end: str) -> Iterable[dict]:
        ...


@runtime_checkable
class Strategy(Protocol):
    def on_bar(self, bar: dict) -> dict:
        ...


@runtime_checkable
class Portfolio(Protocol):
    history: list[dict]

    def generate_orders(self, signal: dict, bar: dict) -> Iterable[dict]:
        ...

    def execute_orders(self, orders: Iterable[dict], bar: dict) -> Iterable[dict]:
        ...

    def update(self, fills: Iterable[dict], bar: dict) -> None:
        ...


@runtime_checkable
class Reporter(Protocol):
    def generate(self, history: Iterable[dict]) -> None:
        ...

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
