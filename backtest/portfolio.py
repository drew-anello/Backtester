from dataclasses import dataclass, field


@dataclass
class Portfolio:
    cash: float
    positions: dict[str, float] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)

    def generate_orders(self, signal, bar):
        # placeholder: convert signal to orders
        return []

    def execute_orders(self, orders, bar):
        # placeholder execution
        return orders

    def update(self, fills, bar):
        # update cash/positions/history
        self.history.append({"bar": bar, "value": self.total_value()})

    def total_value(self) -> float:
        return self.cash + sum(self.positions.values())
