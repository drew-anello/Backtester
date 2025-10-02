from dataclasses import dataclass, field


@dataclass
class Portfolio:
    cash: float
    quantity: float = 0.0  # single-asset quantity for demo
    history: list[dict] = field(default_factory=list)

    def total_value(self, price: float | None = None) -> float:
        if price is None:
            # Value without current price isn't meaningful; used only after update
            return self.cash
        return self.cash + self.quantity * price

    def generate_orders(self, signal, bar):
        """Convert a target weight into an order quantity.

        Expected signal: {"target_weight": float in [0,1]} for a single asset.
        """
        target_w = float(signal.get("target_weight", 0.0))
        price = float(bar.get("close"))
        # Desired notional exposure
        cur_value = self.total_value(price)
        target_notional = target_w * cur_value
        current_notional = self.quantity * price
        delta_notional = target_notional - current_notional
        order_qty = delta_notional / price if price > 0 else 0.0
        return [{"qty": order_qty, "price": price}]

    def execute_orders(self, orders, bar):
        price = float(bar.get("close"))
        fills = []
        for o in orders:
            qty = float(o["qty"])  # market fill at close for demo
            cost = qty * price
            self.cash -= cost
            self.quantity += qty
            fills.append({"qty": qty, "price": price})
        return fills

    def update(self, fills, bar):
        price = float(bar.get("close"))
        value = self.cash + self.quantity * price
        self.history.append({
            "date": bar.get("date"),
            "price": price,
            "cash": self.cash,
            "quantity": self.quantity,
            "value": value,
        })
